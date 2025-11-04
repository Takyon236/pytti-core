"""
PyTTI Image Models
Supports both legacy and modern image generation backends
"""

# Core base classes
from pytti.image_models.differentiable_image import DifferentiableImage
from pytti.image_models.ema import EMAImage

# Legacy image models (preserved for compatibility)
from pytti.image_models.pixel import PixelImage
from pytti.image_models.rgb_image import RGBImage
from pytti.image_models.vqgan import VQGANImage

# Modern diffusion models (NEW!)
try:
    from pytti.image_models.diffusion import (
        StableDiffusionImage,
        FluxImage,
        create_diffusion_image,
    )
    DIFFUSION_AVAILABLE = True
except ImportError as e:
    # Diffusion models require additional dependencies
    DIFFUSION_AVAILABLE = False
    import warnings
    warnings.warn(
        f"Diffusion models not available: {e}\n"
        "Install with: pip install diffusers transformers accelerate"
    )

# Export all
__all__ = [
    # Base classes
    "DifferentiableImage",
    "EMAImage",
    # Legacy models
    "PixelImage",
    "RGBImage",
    "VQGANImage",
]

# Add modern models if available
if DIFFUSION_AVAILABLE:
    __all__.extend([
        "StableDiffusionImage",
        "FluxImage",
        "create_diffusion_image",
    ])
