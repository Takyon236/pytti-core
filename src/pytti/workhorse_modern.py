"""
Modern Workhorse Integration
Bridge between new modern models and existing PyTTI workhorse.py

This module provides helper functions to seamlessly integrate modern models
(Stable Diffusion, Depth-Anything-V2, SAM 2) into the existing PyTTI pipeline
without breaking backward compatibility.
"""

from pathlib import Path
from typing import Optional, Any
from omegaconf import DictConfig

import torch
from loguru import logger
from PIL import Image

from pytti import fetch, vram_usage_mode
from pytti.image_models import PixelImage, RGBImage, VQGANImage


def create_image_model(params: DictConfig, device: torch.device):
    """
    Create image model based on config
    Supports both legacy and modern models

    Args:
        params: Hydra config object
        device: Device to create model on

    Returns:
        Image model instance (PixelImage, RGBImage, VQGANImage, or DiffusionImage)
    """
    image_model_name = params.image_model

    logger.info(f"Creating image model: {image_model_name}")

    # Legacy models
    if image_model_name == "Limited Palette":
        return _create_pixel_image(params, device)

    elif image_model_name == "Unlimited Palette":
        return _create_rgb_image(params, device)

    elif image_model_name == "VQGAN":
        return _create_vqgan_image(params, device)

    # Modern diffusion models
    elif image_model_name in [
        "Stable Diffusion 1.5",
        "Stable Diffusion XL",
        "SDXL Turbo",
        "Stable Diffusion 3.5",
        "Flux Schnell",
        "Flux Dev",
    ]:
        return _create_diffusion_image(params, device)

    else:
        logger.error(f"Unknown image model: {image_model_name}")
        logger.info("Supported models:")
        logger.info("  Legacy: Limited Palette, Unlimited Palette, VQGAN")
        logger.info("  Modern: Stable Diffusion 1.5, Stable Diffusion XL, SDXL Turbo, Flux Schnell, Flux Dev")
        raise ValueError(f"Unknown image model: {image_model_name}")


def _create_pixel_image(params: DictConfig, device: torch.device) -> PixelImage:
    """Create Limited Palette (PixelImage) model"""
    logger.debug("Initializing Limited Palette image model")

    img = PixelImage(
        width=params.width,
        height=params.height,
        scale=params.pixel_size,
        pallet_size=params.palette_size,
        n_pallets=params.palettes,
        gamma=params.gamma,
        hdr_weight=params.hdr_weight,
        norm_weight=params.palette_normalization_weight,
        device=device,
    )

    img.encode_random(random_pallet=params.random_initial_palette)

    if params.target_palette.strip() != "":
        img.set_pallet_target(
            Image.open(fetch(params.target_palette)).convert("RGB")
        )
    else:
        img.lock_pallet(params.lock_palette)

    return img


def _create_rgb_image(params: DictConfig, device: torch.device) -> RGBImage:
    """Create Unlimited Palette (RGBImage) model"""
    logger.debug("Initializing Unlimited Palette image model")

    img = RGBImage(
        params.width,
        params.height,
        params.pixel_size,
        device=device
    )
    img.encode_random()

    return img


def _create_vqgan_image(params: DictConfig, device: torch.device) -> VQGANImage:
    """Create VQGAN image model"""
    logger.debug(f"Initializing VQGAN image model: {params.vqgan_model}")

    model_artifacts_path = Path(params.models_parent_dir) / "vqgan"
    VQGANImage.init_vqgan(params.vqgan_model, model_artifacts_path, device=device)

    img = VQGANImage(
        params.width,
        params.height,
        params.pixel_size,
        device=device
    )
    img.encode_random()

    return img


def _create_diffusion_image(params: DictConfig, device: torch.device):
    """Create modern diffusion image model (SD, SDXL, Flux)"""
    try:
        from pytti.image_models.diffusion import create_diffusion_image
    except ImportError as e:
        logger.error(
            "Diffusion models not available. Install with:\n"
            "  pip install diffusers transformers accelerate"
        )
        raise ImportError(
            "Diffusion models require additional dependencies. "
            "Install with: pip install diffusers transformers accelerate"
        ) from e

    # Map image model names to model IDs
    model_id_map = {
        "Stable Diffusion 1.5": "sd_1.5",
        "Stable Diffusion XL": "sdxl",
        "SDXL Turbo": "sdxl_turbo",
        "Stable Diffusion 3.5": "sd3.5",
        "Flux Schnell": "flux_schnell",
        "Flux Dev": "flux_dev",
    }

    model_id = model_id_map.get(params.image_model)
    if not model_id:
        # Fallback to diffusion_model_id if set
        model_id = params.get("diffusion_model_id", "sdxl")

    logger.debug(f"Initializing diffusion model: {model_id}")

    # Get variant (fp16/fp32)
    variant = "fp16" if params.get("use_fp16", True) and device.type == "cuda" else "fp32"

    img = create_diffusion_image(
        width=params.width,
        height=params.height,
        model=model_id,
        device=device,
        scale=params.get("pixel_size", 1),
        ema_val=0.99,
    )

    # Initialize
    if params.init_image and params.init_image.strip():
        # Initialize from image
        init_image_pil = Image.open(fetch(params.init_image)).convert("RGB")
        img.encode_image(init_image_pil)
    else:
        # Random initialization
        img.encode_random()

    logger.info(f"  Model: {model_id}")
    logger.info(f"  Size: {params.width}x{params.height}")
    logger.info(f"  Precision: {variant}")

    return img


def init_depth_estimation(params: DictConfig, device: torch.device):
    """
    Initialize depth estimation model based on config
    Supports both legacy (AdaBins) and modern (Depth-Anything-V2) models

    Args:
        params: Hydra config object
        device: Device to initialize on
    """
    depth_model = params.get("depth_model", "depth_anything_v2")

    if depth_model == "adabins":
        # Legacy AdaBins
        logger.info("Initializing legacy AdaBins depth model")
        try:
            from pytti.LossAug.DepthLossClass import init_AdaBins
            init_AdaBins(device=device)
        except ImportError:
            logger.warning(
                "AdaBins not available. Using Depth-Anything-V2 instead.\n"
                "Install AdaBins with: pip install ./vendor/AdaBins"
            )
            depth_model = "depth_anything_v2"

    if depth_model in ["depth_anything_v2", "marigold", "zoedepth"]:
        # Modern depth models
        logger.info(f"Initializing modern depth model: {depth_model}")

        try:
            from pytti.depth_models import init_depth_model

            model_size = params.get("depth_model_size", "base")
            init_depth_model(
                model_type=depth_model,
                model_size=model_size,
                device=device,
            )

            logger.info(f"  Depth model: {depth_model} ({model_size})")

        except ImportError as e:
            logger.error(
                f"Modern depth models not available: {e}\n"
                "Install with: pip install transformers timm"
            )
            raise


def init_segmentation(params: DictConfig, device: torch.device):
    """
    Initialize segmentation model (SAM 2) if AI rotoscoping is enabled

    Args:
        params: Hydra config object
        device: Device to initialize on
    """
    if not params.get("use_ai_rotoscoping", False):
        return

    segmentation_model = params.get("segmentation_model", "sam2_base")

    logger.info(f"Initializing AI segmentation: {segmentation_model}")

    try:
        from pytti.rotoscoper_v2 import SAM2Segmenter

        # Extract model size from name (sam2_tiny -> tiny)
        model_size = segmentation_model.replace("sam2_", "")

        # Pre-load the model
        segmenter = SAM2Segmenter(model_size=model_size, device=device)
        segmenter.load_model()

        logger.info(f"  Segmentation model: {segmentation_model}")

    except ImportError as e:
        logger.error(
            f"SAM 2 not available: {e}\n"
            "Install with: pip install git+https://github.com/facebookresearch/segment-anything-2.git"
        )
        raise


def setup_modern_models(params: DictConfig, device: torch.device):
    """
    One-stop setup for all modern models
    Call this early in workhorse.py to initialize everything

    Args:
        params: Hydra config object
        device: Device to use

    Returns:
        Dictionary with initialized components
    """
    logger.info("Setting up modern PyTTI models...")

    components = {}

    # 1. Create image model
    with vram_usage_mode("Image Model Setup"):
        components["image_model"] = create_image_model(params, device)

    # 2. Initialize depth model (if using 3D mode)
    if params.animation_mode == "3D":
        with vram_usage_mode("Depth Model Setup"):
            init_depth_estimation(params, device)

    # 3. Initialize segmentation (if using AI rotoscoping)
    if params.get("use_ai_rotoscoping", False):
        with vram_usage_mode("Segmentation Setup"):
            init_segmentation(params, device)

    logger.info("Modern models ready!")

    return components


def get_model_learning_rate(params: DictConfig) -> float:
    """
    Get appropriate learning rate for the model
    Different models need different learning rates

    Args:
        params: Hydra config object

    Returns:
        Learning rate value
    """
    # If explicitly set, use that
    if params.learning_rate is not None:
        return params.learning_rate

    # Auto-determine based on model
    image_model = params.image_model

    if image_model in ["Stable Diffusion XL", "Stable Diffusion 3.5"]:
        return 0.1  # SDXL latent space
    elif image_model in ["Flux Schnell", "Flux Dev"]:
        return 0.05  # Flux needs lower LR
    elif image_model == "Stable Diffusion 1.5":
        return 0.15  # SD 1.5 can handle higher
    elif image_model == "VQGAN":
        return 0.1  # Original VQGAN LR
    else:
        return 0.2  # Default for RGB/Pixel models


def validate_modern_config(params: DictConfig) -> bool:
    """
    Validate that modern config has all required fields
    Helps users catch config errors early

    Args:
        params: Hydra config object

    Returns:
        True if valid, raises ValueError if not
    """
    errors = []

    # Check image model
    valid_image_models = [
        "Limited Palette",
        "Unlimited Palette",
        "VQGAN",
        "Stable Diffusion 1.5",
        "Stable Diffusion XL",
        "SDXL Turbo",
        "Stable Diffusion 3.5",
        "Flux Schnell",
        "Flux Dev",
    ]

    if params.image_model not in valid_image_models:
        errors.append(
            f"Unknown image_model: {params.image_model}\n"
            f"  Valid options: {', '.join(valid_image_models)}"
        )

    # Check depth model if using 3D
    if params.animation_mode == "3D":
        valid_depth_models = ["depth_anything_v2", "marigold", "zoedepth", "adabins"]
        depth_model = params.get("depth_model", "depth_anything_v2")

        if depth_model not in valid_depth_models:
            errors.append(
                f"Unknown depth_model: {depth_model}\n"
                f"  Valid options: {', '.join(valid_depth_models)}"
            )

    # Check segmentation if using AI rotoscoping
    if params.get("use_ai_rotoscoping", False):
        valid_seg_models = ["sam2_tiny", "sam2_small", "sam2_base", "sam2_large"]
        seg_model = params.get("segmentation_model", "sam2_base")

        if seg_model not in valid_seg_models:
            errors.append(
                f"Unknown segmentation_model: {seg_model}\n"
                f"  Valid options: {', '.join(valid_seg_models)}"
            )

    # Check dimensions
    if params.width <= 0 or params.height <= 0:
        errors.append(
            f"Invalid dimensions: {params.width}x{params.height}\n"
            "  Both width and height must be positive"
        )

    # Raise if errors found
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.debug("Configuration validated successfully")
    return True


# Export main functions
__all__ = [
    "create_image_model",
    "init_depth_estimation",
    "init_segmentation",
    "setup_modern_models",
    "get_model_learning_rate",
    "validate_modern_config",
]
