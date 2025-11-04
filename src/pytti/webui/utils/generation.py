"""
Generation utilities for PyTTI Web UI

Interfaces between Gradio UI and PyTTI's core generation pipeline.
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
        # Reset stop flag
        shared_state.reset_stop_flag()

        # Update state
        shared_state.update_generation_state(
            is_generating=True,
            current_step=0,
            total_steps=config["steps_per_scene"],
        )

        # Create output directory
        output_dir = Path("outputs") / config["file_namespace"]
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting generation: {config['prompt'][:50]}...")

        # 1. Initialize image model
        logger.info(f"Loading image model: {config['diffusion_model']}")

        model_loader = shared_state.get_model_loader()

        # Map UI model names to model IDs
        model_map = {
            "Stable Diffusion XL": "sdxl",
            "Flux Schnell": "flux_schnell",
            "Flux Dev": "flux_dev",
            "Stable Diffusion 1.5": "sd_1.5",
        }

        model_id = model_map.get(config["diffusion_model"], "sdxl")

        # Create image model
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

        logger.info("Image model loaded successfully")

        # 2. Initialize random latent
        logger.info("Initializing random latent...")
        if config["seed"] >= 0:
            torch.manual_seed(config["seed"])
            np.random.seed(config["seed"])

        img_model.encode_random()

        # 3. Initialize CLIP embedder
        logger.info("Loading CLIP model...")
        clip_embedder = HDMultiClipEmbedder(
            cutn=config["cutouts"],
            cut_pow=config["cut_pow"],
            device=shared_state.device,
        )

        # 4. Parse prompt
        logger.info(f"Parsing prompt: {config['prompt']}")
        prompt_obj = parse_prompt(clip_embedder, config["prompt"])

        # 5. Optimize! (PyTTI's magic - iterative refinement)
        logger.info(f"Starting iterative optimization ({config['steps_per_scene']} steps)...")

        learning_rate = config["learning_rate"]
        steps = config["steps_per_scene"]

        for step in range(steps):
            # Check if we should stop
            if shared_state.check_should_stop():
                logger.info("Generation stopped by user")
                break

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
                    intermediate_path = output_dir / f"{config['file_namespace']}_step_{step+1:04d}.png"
                    intermediate_image = img_model.decode_image()
                    intermediate_image.save(intermediate_path)
                    logger.info(f"Saved intermediate result: {intermediate_path}")

            except Exception as e:
                logger.error(f"Error in optimization step {step}: {e}")
                # Continue to next step
                continue

        # 6. Decode final image
        logger.info("Decoding final image...")
        result_image = img_model.decode_image()

        # 7. Save final result
        output_path = output_dir / f"{config['file_namespace']}_final.png"
        result_image.save(output_path)
        logger.info(f"Saved final result: {output_path}")

        # Update state
        shared_state.update_generation_state(
            is_generating=False,
            current_image=result_image,
        )

        # Add to history
        shared_state.history.add_output(
            image_path=output_path,
            prompt=config["prompt"],
            settings=config,
        )

        return result_image, output_path, "Generation complete!"

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        logger.error(traceback.format_exc())

        # Update state
        shared_state.update_generation_state(
            is_generating=False,
            error_message=str(e),
        )

        return None, None, f"Generation failed: {str(e)}"


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
