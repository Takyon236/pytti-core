"""
Generation utilities for PyTTI Web UI (Version 2)

Clean interface using the new GenerationPipeline class.
Much simpler orchestration with better separation of concerns.

This is the new implementation that uses the GenerationPipeline class.
The old generate_image() function is kept for compatibility but will be
deprecated in favor of this cleaner approach.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable
import traceback

import torch
from PIL import Image
from loguru import logger

from pytti.webui.components.shared_state import SharedState
from pytti.pipeline import GenerationPipeline, GenerationConfig
from pytti.managers import ClipManager
from pytti.exceptions import (
    ModelLoadError,
    InvalidConfigError,
    VRAMError,
    GenerationError,
    PromptParseError,
    FileIOError,
    PyTTIException,
)


def generate_image_v2(
    config: Dict[str, Any],
    shared_state: SharedState,
    progress_callback: Optional[Callable[[tuple[int, int], str], None]] = None,
) -> Tuple[Optional[Image.Image], Optional[Path], str]:
    """
    Generate image using PyTTI's pipeline (Version 2).

    This is the new, cleaner implementation that uses GenerationPipeline.
    Much simpler and easier to maintain than the original generate_image().

    Args:
        config: Generation configuration dictionary
        shared_state: Shared application state
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (result_image, output_path, status_message)

    Example:
        >>> from pytti.webui.components.shared_state import SharedState
        >>> state = SharedState()
        >>> config = {
        ...     "prompt": "a beautiful sunset",
        ...     "width": 1024,
        ...     "height": 1024,
        ...     "steps_per_scene": 100,
        ...     # ... other params
        ... }
        >>> image, path, status = generate_image_v2(config, state)
    """
    try:
        # Reset stop flag
        shared_state.reset_stop_flag()

        # Update state - starting generation
        shared_state.update_generation_state(
            is_generating=True,
            current_step=0,
            total_steps=config.get("steps_per_scene", 100),
        )

        logger.info("=" * 60)
        logger.info("🎨 PYTTI GENERATION - Using Pipeline V2")
        logger.info(f"   Prompt: {config.get('prompt', '')[:50]}...")
        logger.info(f"   Size: {config.get('width', 1024)}x{config.get('height', 1024)}")
        logger.info(f"   Steps: {config.get('steps_per_scene', 100)}")
        logger.info("=" * 60)

        # ========================================
        # Create and run pipeline
        # ========================================

        # Cast config to GenerationConfig type
        generation_config: GenerationConfig = config  # type: ignore

        # Create pipeline
        pipeline = GenerationPipeline(
            config=generation_config,
            device=shared_state.device,
            progress_callback=progress_callback,
        )

        # Run pipeline (all steps handled internally)
        result_image, output_path = pipeline.run()

        # ========================================
        # Update shared state with results
        # ========================================

        shared_state.update_generation_state(
            is_generating=False,
            current_image=result_image,
        )

        # Add to history
        try:
            shared_state.history.add_output(
                image_path=output_path,
                prompt=config["prompt"],
                settings=config,
            )
        except Exception as e:
            logger.warning(f"Failed to add to history: {e}")
            # Don't fail generation if history fails

        return result_image, output_path, "✅ Generation complete!"

    # ========================================
    # Exception Handling
    # ========================================

    except (
        ModelLoadError,
        VRAMError,
        PromptParseError,
        FileIOError,
        GenerationError,
        InvalidConfigError,
    ) as e:
        # Our custom exceptions with user-friendly messages
        logger.error(f"Generation failed: {e.message}")
        logger.error(traceback.format_exc())

        # Update state
        shared_state.update_generation_state(
            is_generating=False,
            error_message=e.get_user_message(),
        )

        return None, None, f"❌ {e.get_user_message()}"

    except torch.cuda.OutOfMemoryError as e:
        # VRAM error
        error = VRAMError()
        logger.error(f"VRAM error: {e}")
        logger.error(traceback.format_exc())

        # Try to free VRAM
        try:
            torch.cuda.empty_cache()
            ClipManager.get_instance().cleanup()
        except Exception:
            pass

        shared_state.update_generation_state(
            is_generating=False,
            error_message=error.get_user_message(),
        )

        return None, None, f"❌ {error.get_user_message()}"

    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error during generation: {e}")
        logger.error(traceback.format_exc())

        error_message = (
            f"An unexpected error occurred: {str(e)}\n\n"
            "💡 This might be a bug. Please check the console for details."
        )

        shared_state.update_generation_state(
            is_generating=False,
            error_message=error_message,
        )

        return None, None, f"❌ {error_message}"


def estimate_generation_time(
    width: int,
    height: int,
    steps: int,
    device: torch.device,
) -> str:
    """
    Estimate generation time based on parameters.

    Args:
        width: Image width
        height: Image height
        steps: Number of optimization steps
        device: PyTorch device

    Returns:
        Human-readable time estimate

    Example:
        >>> device = torch.device("cuda")
        >>> estimate = estimate_generation_time(1024, 1024, 100, device)
        >>> print(estimate)  # "~2 minutes"
    """
    # Rough estimates based on typical hardware
    if device.type == "cuda":
        # GPU estimates
        try:
            memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3

            if memory_gb >= 16:
                # High-end GPU (RTX 3090, 4090, etc.)
                seconds_per_step = 0.5
            elif memory_gb >= 8:
                # Mid-range GPU (RTX 3060, etc.)
                seconds_per_step = 1.0
            else:
                # Low-end GPU
                seconds_per_step = 2.0
        except Exception:
            # Default if can't get properties
            seconds_per_step = 1.0
    else:
        # CPU estimates (very slow)
        seconds_per_step = 10.0

    # Adjust for resolution
    resolution_factor = (width * height) / (1024 * 1024)
    adjusted_time = steps * seconds_per_step * resolution_factor

    # Format as human-readable
    if adjusted_time < 60:
        return f"~{int(adjusted_time)} seconds"
    elif adjusted_time < 3600:
        return f"~{int(adjusted_time / 60)} minutes"
    else:
        return f"~{int(adjusted_time / 3600)} hours"
