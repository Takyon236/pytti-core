"""
Modern Depth Estimation Models for PyTTI
Preserves PyTTI's unique 3D camera transform algorithms

This module provides modern depth estimation while maintaining compatibility
with PyTTI's existing 3D effects in Transforms.py (render_image_3d, zoom_3d)
"""

from __future__ import annotations

import math
from typing import Optional, Tuple, Union
from pathlib import Path

import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from torchvision.transforms import functional as TF
from loguru import logger

from pytti import vram_usage_mode


class BaseDepthEstimator:
    """
    Base class for depth estimators
    Provides unified interface for PyTTI's 3D transform system
    """

    def __init__(self, device: Optional[torch.device] = None):
        """Initialize depth estimator"""
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.device = device
        self.model = None

    @torch.no_grad()
    def estimate_depth(
        self,
        image: Union[Image.Image, torch.Tensor],
        resize_for_model: bool = True,
    ) -> Tuple[np.ndarray, bool]:
        """
        Estimate depth map from image

        Args:
            image: Input image (PIL or tensor)
            resize_for_model: Whether to resize for model constraints

        Returns:
            Tuple of (depth_map as numpy array, was_resized bool)
        """
        raise NotImplementedError("Subclass must implement estimate_depth")

    def load_model(self):
        """Load the depth estimation model"""
        raise NotImplementedError("Subclass must implement load_model")


class DepthAnythingV2(BaseDepthEstimator):
    """
    Depth Anything V2 - State-of-the-art depth estimation (2024)
    Replaces AdaBins while maintaining API compatibility

    Paper: https://arxiv.org/abs/2406.09414
    Repo: https://github.com/DepthAnything/Depth-Anything-V2
    """

    def __init__(
        self,
        model_size: str = "base",
        device: Optional[torch.device] = None,
    ):
        """
        Initialize Depth Anything V2

        Args:
            model_size: Model size (small, base, large)
            device: Device to run on
        """
        super().__init__(device)
        self.model_size = model_size
        self.model_id = f"depth_anything_v2_{model_size}"
        self.max_depth_area = 500000  # Match PyTTI's original constraint

    def load_model(self):
        """Load Depth Anything V2 model"""
        if self.model is not None:
            return

        logger.info(f"Loading Depth Anything V2 ({self.model_size})")

        with vram_usage_mode("Depth Anything V2"):
            try:
                # Try loading from transformers (if available)
                from transformers import AutoImageProcessor, AutoModelForDepthEstimation

                model_name = f"depth-anything/Depth-Anything-V2-{self.model_size.capitalize()}"

                self.processor = AutoImageProcessor.from_pretrained(model_name)
                self.model = AutoModelForDepthEstimation.from_pretrained(model_name)
                self.model = self.model.to(self.device)
                self.model.eval()

                logger.info(f"  Loaded from transformers: {model_name}")

            except ImportError:
                # Fallback to direct implementation
                logger.warning("transformers not available, using direct implementation")
                self._load_direct()

    def _load_direct(self):
        """
        Direct loading of Depth Anything V2
        Fallback if transformers is not available
        """
        # This would load the model directly from checkpoint
        # For now, we'll require transformers
        raise ImportError(
            "Depth Anything V2 requires transformers library. "
            "Install with: pip install transformers"
        )

    @torch.no_grad()
    def estimate_depth(
        self,
        image: Union[Image.Image, torch.Tensor],
        resize_for_model: bool = True,
    ) -> Tuple[np.ndarray, bool]:
        """
        Estimate depth map from image
        Compatible with PyTTI's existing 3D transform system

        Args:
            image: Input image
            resize_for_model: Whether to resize for model constraints

        Returns:
            Tuple of (depth_map, was_resized)
        """
        # Load model if not loaded
        if self.model is None:
            self.load_model()

        # Convert to PIL if tensor
        if isinstance(image, torch.Tensor):
            image = TF.to_pil_image(image)

        width, height = image.size
        image_area = width * height
        depth_resized = False

        # Resize if image is too large (PyTTI compatibility)
        if resize_for_model and image_area > self.max_depth_area:
            depth_scale_factor = math.sqrt(self.max_depth_area / image_area)
            new_width = int(width * depth_scale_factor)
            new_height = int(height * depth_scale_factor)
            depth_input = image.resize((new_width, new_height), Image.LANCZOS)
            depth_resized = True
        else:
            depth_input = image

        # Prepare inputs
        inputs = self.processor(images=depth_input, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Predict depth
        with vram_usage_mode("Depth Prediction"):
            outputs = self.model(**inputs)
            predicted_depth = outputs.predicted_depth

        # Convert to numpy and resize to original size if needed
        depth_map = predicted_depth.squeeze().cpu().numpy()

        return depth_map, depth_resized

    @staticmethod
    def get_depth(
        pil_image: Image.Image,
        device: Optional[torch.device] = None,
        model_size: str = "base",
    ) -> Tuple[np.ndarray, bool]:
        """
        Static method for compatibility with PyTTI's existing code
        Drop-in replacement for AdaBins.get_depth()

        Args:
            pil_image: Input PIL image
            device: Device to run on
            model_size: Model size to use

        Returns:
            Tuple of (depth_map, was_resized)
        """
        # Get or create global instance
        global _global_depth_estimator

        if _global_depth_estimator is None:
            _global_depth_estimator = DepthAnythingV2(
                model_size=model_size,
                device=device,
            )

        return _global_depth_estimator.estimate_depth(pil_image)


class MarigoldDepth(BaseDepthEstimator):
    """
    Marigold - Diffusion-based depth estimation
    Higher quality but slower than Depth Anything V2

    Paper: https://arxiv.org/abs/2312.02145
    Repo: https://github.com/prs-eth/marigold
    """

    def __init__(self, device: Optional[torch.device] = None):
        """Initialize Marigold depth estimator"""
        super().__init__(device)
        self.model_id = "prs-eth/marigold-v1-0"

    def load_model(self):
        """Load Marigold model"""
        if self.model is not None:
            return

        logger.info("Loading Marigold depth estimator")

        with vram_usage_mode("Marigold"):
            try:
                from diffusers import MarigoldDepthPipeline

                self.model = MarigoldDepthPipeline.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                )
                self.model = self.model.to(self.device)

                logger.info("  Marigold loaded successfully")

            except ImportError:
                raise ImportError(
                    "Marigold requires diffusers library. "
                    "Install with: pip install diffusers"
                )

    @torch.no_grad()
    def estimate_depth(
        self,
        image: Union[Image.Image, torch.Tensor],
        resize_for_model: bool = True,
    ) -> Tuple[np.ndarray, bool]:
        """Estimate depth with Marigold (slower but higher quality)"""
        if self.model is None:
            self.load_model()

        if isinstance(image, torch.Tensor):
            image = TF.to_pil_image(image)

        with vram_usage_mode("Marigold Depth Prediction"):
            # Marigold returns depth in meters (metric depth)
            depth = self.model(image)
            depth_map = depth.prediction.squeeze().cpu().numpy()

        return depth_map, False


# Global depth estimator instance (singleton pattern)
_global_depth_estimator: Optional[BaseDepthEstimator] = None


def init_depth_model(
    model_type: str = "depth_anything_v2",
    model_size: str = "base",
    device: Optional[torch.device] = None,
):
    """
    Initialize depth estimation model
    Replaces init_AdaBins() from original PyTTI

    Args:
        model_type: Type of depth model (depth_anything_v2, marigold)
        model_size: Model size (for depth_anything_v2: small, base, large)
        device: Device to run on
    """
    global _global_depth_estimator

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if model_type == "depth_anything_v2":
        _global_depth_estimator = DepthAnythingV2(model_size=model_size, device=device)
    elif model_type == "marigold":
        _global_depth_estimator = MarigoldDepth(device=device)
    else:
        raise ValueError(f"Unknown depth model type: {model_type}")

    # Preload the model
    _global_depth_estimator.load_model()


def get_depth_estimator() -> BaseDepthEstimator:
    """Get the global depth estimator instance"""
    global _global_depth_estimator

    if _global_depth_estimator is None:
        # Initialize with default if not set
        init_depth_model()

    return _global_depth_estimator


def estimate_depth(
    image: Union[Image.Image, torch.Tensor],
    model_type: Optional[str] = None,
    **kwargs,
) -> Tuple[np.ndarray, bool]:
    """
    Convenience function to estimate depth
    Automatically handles model initialization

    Args:
        image: Input image
        model_type: Optional model type to use
        **kwargs: Additional arguments

    Returns:
        Tuple of (depth_map, was_resized)
    """
    if model_type and _global_depth_estimator is None:
        init_depth_model(model_type=model_type)

    estimator = get_depth_estimator()
    return estimator.estimate_depth(image, **kwargs)


# Export main classes and functions
__all__ = [
    "BaseDepthEstimator",
    "DepthAnythingV2",
    "MarigoldDepth",
    "init_depth_model",
    "get_depth_estimator",
    "estimate_depth",
]
