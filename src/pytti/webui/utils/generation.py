"""
Generation utilities for PyTTI Web UI

Interfaces between Gradio UI and PyTTI's core generation pipeline.

Now includes:
- Comprehensive error handling with user-friendly messages
- Input validation to prevent crashes
- Model caching for better performance
- Proper resource cleanup
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable
import traceback

import torch
import numpy as np
from PIL import Image
from loguru import logger

from pytti.webui.components.shared_state import SharedState
from pytti.image_models.diffusion import StableDiffusionImage, FluxImage
from pytti.Perceptor.Embedder import HDMultiClipEmbedder
from pytti.Perceptor.Prompt import parse_prompt
from pytti.managers import ClipManager, ModelManager, ModelType
from pytti.exceptions import (
    ModelLoadError,
    InvalidConfigError,
    VRAMError,
    GenerationError,
    PromptParseError,
    FileIOError,
)
from pytti.validation import ConfigValidator


def generate_image(
    config: Dict[str, Any],
    shared_state: SharedState,
    progress_callback: Optional[Callable] = None,
) -> Tuple[Optional[Image.Image], Optional[Path], str]:
    """
    Generate image using PyTTI's iterative optimization

    Args:
        config: Generation configuration
        shared_state: Shared application state
        progress_callback: Optional progress callback

    Returns:
        Tuple of (result_image, output_path, status_message)
    """
    try:
        # ========================================
        # STEP 0: Validate Configuration
        # ========================================
        logger.info("Validating configuration...")
        try:
            ConfigValidator.validate_and_raise(config)
            logger.info("✓ Configuration validated")
        except InvalidConfigError as e:
            logger.error(f"Configuration validation failed: {e.get_user_message()}")
            return None, None, f"❌ Invalid settings:\n{e.get_user_message()}"

        # Reset stop flag
        shared_state.reset_stop_flag()

        # Update state
        shared_state.update_generation_state(
            is_generating=True,
            current_step=0,
            total_steps=config["steps_per_scene"],
        )

        # Create output directory with error handling
        try:
            output_dir = Path("outputs") / config["file_namespace"]
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory: {output_dir}")
        except Exception as e:
            raise FileIOError("create", str(output_dir), e)

        logger.info(f"Starting generation: {config['prompt'][:50]}...")

        # ========================================
        # STEP 1: Initialize Diffusion Model
        # ========================================
        logger.info(f"Loading diffusion model: {config['diffusion_model']}")

        try:
            model_loader = shared_state.get_model_loader()

            # Map UI model names to model IDs
            model_map = {
                "Stable Diffusion XL": "sdxl",
                "Flux Schnell": "flux_schnell",
                "Flux Dev": "flux_dev",
                "Stable Diffusion 1.5": "sd_1.5",
            }

            model_id = model_map.get(config["diffusion_model"], "sdxl")

            # Create image model with error handling
            if "Flux" in config["diffusion_model"]:
                img_model = FluxImage(
                    width=config["width"],
                    height=config["height"],
                    model_id=model_id,
                    ema_val=config["ema_val"],
                    device=shared_state.device,
                )
            else:
                img_model = StableDiffusionImage(
                    width=config["width"],
                    height=config["height"],
                    model_id=model_id,
                    ema_val=config["ema_val"],
                    device=shared_state.device,
                )

            logger.info("✓ Diffusion model loaded successfully")

        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"VRAM error loading model: {e}")
            raise VRAMError()
        except Exception as e:
            logger.error(f"Failed to load diffusion model: {e}")
            raise ModelLoadError(config["diffusion_model"], e)

        # ========================================
        # STEP 2: Initialize Random Latent
        # ========================================
        logger.info("Initializing random latent...")
        if config["seed"] >= 0:
            torch.manual_seed(config["seed"])
            np.random.seed(config["seed"])
            logger.info(f"Using seed: {config['seed']}")

        img_model.encode_random()
        logger.info("✓ Random latent initialized")

        # ========================================
        # STEP 3: Initialize CLIP Perceptors
        # ========================================
        logger.info("Loading CLIP model...")
        try:
            clip_manager = ClipManager.get_instance()

            # Get CLIP model from config, default to ViT-B/32
            clip_model_name = config.get("clip_model", "ViT-B/32")

            # Map UI names to model names
            clip_model_map = {
                "ViT-B/32 (Fast)": "ViT-B/32",
                "ViT-B/16 (Balanced)": "ViT-B/16",
                "ViT-L/14 (Quality)": "ViT-L/14",
                "SigLIP (Recommended)": "ViT-B/16",  # SigLIP fallback to ViT-B/16 for now
            }

            clip_model = clip_model_map.get(clip_model_name, clip_model_name)
            clip_models = [clip_model]

            clip_manager.initialize(clip_models, device=shared_state.device)
            logger.info(f"✓ CLIP model loaded: {clip_model}")

        except Exception as e:
            logger.error(f"Failed to load CLIP: {e}")
            raise ModelLoadError(f"CLIP ({clip_model})", e)

        # ========================================
        # STEP 4: Initialize CLIP Embedder
        # ========================================
        logger.info("Initializing CLIP embedder...")
        try:
            clip_embedder = HDMultiClipEmbedder(
                cutn=config["cutouts"],
                cut_pow=config["cut_pow"],
                device=shared_state.device,
            )
            logger.info("✓ CLIP embedder initialized")
        except Exception as e:
            logger.error(f"Failed to create CLIP embedder: {e}")
            raise ModelLoadError("CLIP Embedder", e)

        # ========================================
        # STEP 5: Parse Prompt
        # ========================================
        logger.info(f"Parsing prompt: {config['prompt']}")
        try:
            prompt_obj = parse_prompt(clip_embedder, config["prompt"])
            logger.info("✓ Prompt parsed successfully")
        except Exception as e:
            logger.error(f"Failed to parse prompt: {e}")
            raise PromptParseError(config["prompt"], e)

        # ========================================
        # STEP 6: Iterative Optimization
        # ========================================
        logger.info(f"Starting iterative optimization ({config['steps_per_scene']} steps)...")

        learning_rate = config["learning_rate"]
        steps = config["steps_per_scene"]
        failed_steps = 0
        max_failed_steps = 10  # Abort if too many failures

        for step in range(steps):
            # Check if we should stop
            if shared_state.check_should_stop():
                logger.info("⏸️  Generation stopped by user")
                break

            # Check if too many failed steps
            if failed_steps >= max_failed_steps:
                logger.error(f"Too many failed steps ({failed_steps}), aborting")
                raise GenerationError(
                    step,
                    Exception(f"Generation unstable: {failed_steps} consecutive failures")
                )

            # Update progress
            shared_state.update_generation_state(current_step=step + 1)

            if progress_callback:
                progress_callback((step + 1, steps), desc=f"Step {step + 1}/{steps}")

            # PyTTI's optimization step
            try:
                # Get current image
                current_latent = img_model.get_image_tensor()

                # Decode for CLIP evaluation
                with torch.no_grad():
                    current_image = img_model.decode(current_latent)

                # Compute CLIP loss
                clip_loss = prompt_obj.compute_loss(current_image)

                # Compute gradients
                if current_latent.grad is not None:
                    current_latent.grad.zero_()

                clip_loss.backward()

                # Update latent with gradient descent
                with torch.no_grad():
                    if current_latent.grad is not None:
                        current_latent -= learning_rate * current_latent.grad

                    # Apply EMA smoothing (PyTTI's temporal coherence)
                    img_model.update_ema()

                # Save intermediate results
                if (step + 1) % config["save_every"] == 0:
                    try:
                        intermediate_path = output_dir / f"{config['file_namespace']}_step_{step+1:04d}.png"
                        intermediate_image = img_model.decode_image()
                        intermediate_image.save(intermediate_path)
                        logger.info(f"💾 Saved: {intermediate_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to save intermediate result: {e}")
                        # Don't abort generation for save failures

                # Reset failed step counter on success
                failed_steps = 0

            except torch.cuda.OutOfMemoryError as e:
                logger.error(f"VRAM error at step {step}: {e}")
                raise VRAMError()

            except Exception as e:
                logger.error(f"Error in optimization step {step}: {e}")
                failed_steps += 1

                # If within tolerance, continue to next step
                if failed_steps < max_failed_steps:
                    logger.warning(f"Continuing... ({failed_steps}/{max_failed_steps} failures)")
                    continue
                else:
                    # Too many failures, abort
                    raise GenerationError(step, e)

        # ========================================
        # STEP 7: Decode & Save Final Image
        # ========================================
        logger.info("Decoding final image...")
        try:
            result_image = img_model.decode_image()
            logger.info("✓ Final image decoded")
        except Exception as e:
            logger.error(f"Failed to decode final image: {e}")
            raise GenerationError(steps, e)

        # Save final result
        try:
            output_path = output_dir / f"{config['file_namespace']}_final.png"
            result_image.save(output_path)
            logger.info(f"✅ Saved final result: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save final image: {e}")
            raise FileIOError("save", str(output_path), e)

        # Update state
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

        logger.info("=" * 60)
        logger.info("✅ GENERATION COMPLETE!")
        logger.info(f"   Prompt: {config['prompt'][:50]}...")
        logger.info(f"   Steps: {steps}")
        logger.info(f"   Output: {output_path}")
        logger.info("=" * 60)

        return result_image, output_path, "✅ Generation complete!"

    # ========================================
    # Exception Handling
    # ========================================
    except (ModelLoadError, VRAMError, PromptParseError, FileIOError, GenerationError, InvalidConfigError) as e:
        # These are our custom exceptions with user-friendly messages
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

        # Update state
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
    Estimate generation time

    Args:
        width: Image width
        height: Image height
        steps: Number of steps
        device: PyTorch device

    Returns:
        Estimated time string
    """
    # Rough estimates based on typical hardware
    if device.type == "cuda":
        # GPU estimates
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
