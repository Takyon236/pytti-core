"""
Stable Diffusion Image Model for PyTTI
Preserves PyTTI's unique CLIP-guided iterative optimization "flavor"

This implementation:
1. Uses SD's latent space for optimization (like VQGAN did)
2. Maintains PyTTI's EMA (Exponential Moving Average) approach
3. Supports CLIP-guided gradients for that distinctive PyTTI aesthetic
4. Compatible with PyTTI's existing loss orchestration system

Inspired by ComfyUI's clean SD integration but adapted for PyTTI's workflow
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union, Literal

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision.transforms import functional as TF
from loguru import logger

from pytti import vram_usage_mode, replace_grad, clamp_with_grad
from pytti.image_models import EMAImage


class StableDiffusionImage(EMAImage):
    """
    Stable Diffusion-based image representation
    Optimizes in SD's latent space with PyTTI's iterative refinement approach

    This preserves PyTTI's unique "flavor" by:
    - Using latent space optimization (not just img2img)
    - Allowing CLIP guidance on decoded images
    - Maintaining temporal coherence for video
    - Supporting EMA for stable optimization
    """

    def __init__(
        self,
        width: int,
        height: int,
        scale: int = 1,
        model_id: str = "sdxl",
        ema_val: float = 0.99,
        device: Optional[torch.device] = None,
        variant: str = "fp16",
    ):
        """
        Initialize Stable Diffusion image model

        Args:
            width: Image width in pixels
            height: Image height in pixels
            scale: Scaling factor
            model_id: Model to use (sd_1.5, sdxl, sd3.5, flux_schnell, flux_dev)
            ema_val: EMA decay value (PyTTI's temporal smoothing)
            device: Device to run on
            variant: Model variant (fp16 or fp32)
        """
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        width *= scale
        height *= scale

        # Import here to avoid circular dependency
        from pytti.model_loader import get_model_loader

        logger.info(f"Initializing {model_id} image model")

        with vram_usage_mode(f"SD Image ({model_id})"):
            # Load diffusion pipeline
            loader = get_model_loader(device=device)
            pipe = loader.load_diffusion_model(model_id, variant=variant)

            # Get VAE for encoding/decoding
            vae = pipe.vae
            vae.eval()
            vae.requires_grad_(False)

            # Calculate latent dimensions
            # SD uses 8x downsampling for latents
            vae_scale_factor = 2 ** (len(vae.config.block_out_channels) - 1)
            latent_width = width // vae_scale_factor
            latent_height = height // vae_scale_factor
            latent_channels = vae.config.latent_channels

            # Initialize random latent
            # SD latents have roughly N(0, 1) distribution after VAE encoding
            latent = torch.randn(
                1,
                latent_channels,
                latent_height,
                latent_width,
                device=device,
                dtype=torch.float32,
            )
            # Scale appropriately for SD's latent space
            latent = latent * vae.config.scaling_factor

            # Initialize EMA image FIRST (before setting module attributes)
            super().__init__(width, height, latent, ema_val)

            # NOW we can set module attributes after super().__init__()
            self.device = device
            self.pipe = pipe
            self.vae = vae
            self.vae_scale_factor = vae_scale_factor

            self.output_axes = ("n", "c", "h", "w")
            self.latent_strength = 1.0  # For latent loss (PyTTI feature)

            # Learning rate (tune for SD latent space)
            self.lr = 0.1

            # Store model info
            self.model_id = model_id
            self.latent_channels = latent_channels
            self.latent_height = latent_height
            self.latent_width = latent_width

        logger.info(f"  Image size: {width}x{height}")
        logger.info(f"  Latent size: {latent_width}x{latent_height}x{latent_channels}")
        logger.info(f"  Device: {device}")

    def _rand_latent(
        self,
        channels: int,
        height: int,
        width: int,
    ) -> torch.Tensor:
        """
        Generate random latent tensor
        Uses appropriate distribution for SD latent space
        """
        # SD latents have roughly N(0, 1) distribution after VAE encoding
        latent = torch.randn(
            1,
            channels,
            height,
            width,
            device=self.device,
            dtype=torch.float32,
        )

        # Scale appropriately for SD's latent space
        # SD's VAE scaling factor
        latent = latent * self.vae.config.scaling_factor

        return latent

    @torch.no_grad()
    def encode_image(self, pil_image: Image.Image, **kwargs):
        """
        Encode a PIL image to latent space
        This is how PyTTI can initialize from an existing image
        """
        # Resize to target size
        pil_image = pil_image.resize(self.image_shape, Image.LANCZOS)

        # Convert to tensor
        image_tensor = TF.to_tensor(pil_image).unsqueeze(0).to(self.device)

        # Normalize to [-1, 1] (SD convention)
        image_tensor = image_tensor * 2 - 1

        # Encode with VAE
        with vram_usage_mode("VAE Encode"):
            latent_dist = self.vae.encode(image_tensor)
            latent = latent_dist.latent_dist.sample()
            latent = latent * self.vae.config.scaling_factor

        # Set our tensor to this latent
        self.tensor.set_(latent)
        self.reset()  # Reset EMA

        logger.debug(f"Encoded image to latent: {latent.shape}")

    @torch.no_grad()
    def encode_random(self):
        """
        Initialize with random latent
        PyTTI's standard initialization for generating from scratch
        """
        latent = self._rand_latent(
            self.latent_channels,
            self.latent_height,
            self.latent_width,
        )
        self.tensor.set_(latent)
        self.reset()

    def decode(self, latent: torch.Tensor, device: Optional[torch.device] = None) -> torch.Tensor:
        """
        Decode latent to image
        This is where PyTTI's CLIP guidance sees the actual image

        Args:
            latent: Latent tensor to decode
            device: Device to decode on

        Returns:
            Decoded image tensor in [0, 1] range
        """
        if device is None:
            device = self.device

        # Ensure latent is on correct device
        latent = latent.to(device)

        # Unscale the latent
        latent = latent / self.vae.config.scaling_factor

        with vram_usage_mode("VAE Decode"):
            # Decode with VAE
            image = self.vae.decode(latent).sample

        # Convert from [-1, 1] to [0, 1]
        image = (image + 1) / 2

        # Clamp with gradient (PyTTI technique)
        image = clamp_with_grad(image, 0, 1)

        return image

    def get_latent_tensor(self, detach: bool = False, device: Optional[torch.device] = None) -> torch.Tensor:
        """
        Get the current latent tensor
        Used by PyTTI's latent loss functions
        """
        if device is None:
            device = self.device

        latent = self.tensor
        if detach:
            latent = latent.detach()

        return latent.to(device)

    @classmethod
    def get_preferred_loss(cls):
        """
        Return the preferred loss class for this image model
        PyTTI uses this for latent space losses
        """
        from pytti.LossAug.LatentLossClass import LatentLoss
        return LatentLoss

    def clone(self):
        """Clone this image model (for backups, etc.)"""
        dummy = StableDiffusionImage(
            *self.image_shape,
            model_id=self.model_id,
            device=self.device,
        )

        with torch.no_grad():
            dummy.tensor.set_(self.tensor.clone())
            dummy.accum.set_(self.accum.clone())
            dummy.biased.set_(self.biased.clone())
            dummy.average.set_(self.average.clone())
            dummy.decay = self.decay

        return dummy

    @staticmethod
    def init_model(
        model_id: str = "sdxl",
        device: Optional[torch.device] = None,
    ):
        """
        Pre-load a diffusion model (optional)
        Similar to VQGANImage.init_vqgan()

        Args:
            model_id: Model to preload
            device: Device to load on
        """
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        from pytti.model_loader import get_model_loader

        logger.info(f"Pre-loading diffusion model: {model_id}")
        loader = get_model_loader(device=device)
        loader.load_diffusion_model(model_id)
        logger.info(f"  Model {model_id} ready")


class FluxImage(StableDiffusionImage):
    """
    Flux-specific image model
    Flux has some architectural differences from SD, handle them here
    """

    def __init__(
        self,
        width: int,
        height: int,
        scale: int = 1,
        model_id: str = "flux_schnell",
        ema_val: float = 0.99,
        device: Optional[torch.device] = None,
    ):
        """Initialize Flux image model"""
        # Flux uses different defaults
        super().__init__(
            width=width,
            height=height,
            scale=scale,
            model_id=model_id,
            ema_val=ema_val,
            device=device,
            variant="fp16",  # Flux typically uses fp16
        )

        # Flux may need different learning rates
        self.lr = 0.05

    # Flux-specific methods can be added here as needed


# Convenience function for backward compatibility
def create_diffusion_image(
    width: int,
    height: int,
    model: Literal["sd_1.5", "sdxl", "sd3.5", "flux_schnell", "flux_dev"] = "sdxl",
    **kwargs,
) -> Union[StableDiffusionImage, FluxImage]:
    """
    Factory function to create the appropriate diffusion image model

    Args:
        width: Image width
        height: Image height
        model: Model type to use
        **kwargs: Additional arguments

    Returns:
        Appropriate image model instance
    """
    if "flux" in model:
        return FluxImage(width, height, model_id=model, **kwargs)
    else:
        return StableDiffusionImage(width, height, model_id=model, **kwargs)
