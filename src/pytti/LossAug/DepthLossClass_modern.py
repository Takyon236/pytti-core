"""
Modernized Depth Loss Class for PyTTI
Supports both legacy AdaBins and modern depth models

Preserves PyTTI's loss calculation approach while allowing modern depth estimation
"""

import gc
import math
from typing import Optional, Literal

from loguru import logger
from PIL import Image
import torch
from torch.nn import functional as F
from torchvision.transforms import functional as TF

from pytti import DEVICE, vram_usage_mode
from pytti.LossAug.MSELossClass import MSELoss


class ModernDepthLoss(MSELoss):
    """
    Depth Loss with modern depth estimation backends

    Supports:
    - depth_anything_v2 (default, recommended)
    - marigold (high quality, slower)
    - adabins (legacy, for compatibility)
    """

    # Class variable for depth model selection
    _depth_model_type: str = "depth_anything_v2"
    _depth_model_size: str = "base"

    @torch.no_grad()
    def set_comp(self, pil_image):
        """Set comparison depth map from image"""
        self.comp.set_(ModernDepthLoss.make_comp(pil_image))
        if self.use_mask and self.mask.shape[-2:] != self.comp.shape[-2:]:
            self.mask.set_(TF.resize(self.mask, self.comp.shape[-2:]))

    def get_loss(self, input, img):
        """
        Calculate depth loss
        Maintains PyTTI's original approach
        """
        height, width = input.shape[-2:]
        max_depth_area = 500000
        image_area = width * height

        # Resize if too large (PyTTI's approach)
        if image_area > max_depth_area:
            depth_scale_factor = math.sqrt(max_depth_area / image_area)
            height, width = int(height * depth_scale_factor), int(
                width * depth_scale_factor
            )
            depth_input = TF.resize(
                input, (height, width), interpolation=TF.InterpolationMode.BILINEAR
            )
        else:
            depth_input = input

        # Estimate depth using modern model
        depth_map = self._estimate_depth_tensor(depth_input)

        # Resize to comparison size
        depth_map = F.interpolate(
            depth_map, self.comp.shape[-2:], mode="bilinear", align_corners=True
        )

        # Use parent MSELoss for actual loss calculation
        return super().get_loss(depth_map, img)

    @torch.no_grad()
    def _estimate_depth_tensor(self, image_tensor: torch.Tensor) -> torch.Tensor:
        """
        Estimate depth from tensor
        Handles device management and model loading
        """
        # Import depth models
        from pytti.depth_models import get_depth_estimator, init_depth_model

        # Initialize depth model if needed
        try:
            depth_estimator = get_depth_estimator()
        except:
            # Initialize with current settings
            init_depth_model(
                model_type=self._depth_model_type,
                model_size=self._depth_model_size,
                device=image_tensor.device,
            )
            depth_estimator = get_depth_estimator()

        # Convert tensor to PIL for depth estimation
        pil_image = TF.to_pil_image(image_tensor.squeeze())

        # Estimate depth
        depth_map_np, _ = depth_estimator.estimate_depth(pil_image)

        # Convert back to tensor
        depth_map = torch.from_numpy(depth_map_np).unsqueeze(0).unsqueeze(0)
        depth_map = depth_map.to(image_tensor.device)

        return depth_map

    @classmethod
    @vram_usage_mode("Depth Loss")
    def make_comp(cls, pil_image, device=None):
        """
        Create comparison depth map from PIL image
        Uses modern depth estimation
        """
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        depth_map, _ = cls.get_depth(pil_image, device=device)
        return torch.from_numpy(depth_map).to(device)

    @staticmethod
    def get_depth(
        pil_image: Image.Image,
        device: Optional[torch.device] = None,
        model_type: Optional[str] = None,
        model_size: Optional[str] = None,
    ):
        """
        Static method for depth estimation
        Drop-in replacement for old AdaBins-based get_depth

        Args:
            pil_image: Input PIL image
            device: Device to run on
            model_type: Depth model type (overrides class default)
            model_size: Model size (for depth_anything_v2)

        Returns:
            Tuple of (depth_map, was_resized)
        """
        from pytti.depth_models import init_depth_model, get_depth_estimator

        # Use provided model type or class default
        if model_type is None:
            model_type = ModernDepthLoss._depth_model_type
        if model_size is None:
            model_size = ModernDepthLoss._depth_model_size

        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Initialize depth model
        try:
            depth_estimator = get_depth_estimator()
        except:
            init_depth_model(
                model_type=model_type,
                model_size=model_size,
                device=device,
            )
            depth_estimator = get_depth_estimator()

        # Estimate depth
        gc.collect()
        torch.cuda.empty_cache()

        depth_map, depth_resized = depth_estimator.estimate_depth(pil_image)

        gc.collect()
        torch.cuda.empty_cache()

        return depth_map, depth_resized

    @classmethod
    def set_depth_model(
        cls,
        model_type: Literal["depth_anything_v2", "marigold", "adabins"] = "depth_anything_v2",
        model_size: Literal["small", "base", "large"] = "base",
    ):
        """
        Configure which depth model to use globally

        Args:
            model_type: Type of depth model
            model_size: Size of model (for depth_anything_v2)
        """
        cls._depth_model_type = model_type
        cls._depth_model_size = model_size
        logger.info(f"Depth model set to: {model_type} ({model_size})")


# Backward compatibility: Keep old DepthLoss name pointing to modern version
DepthLoss = ModernDepthLoss


# Legacy AdaBins support (for backward compatibility)
def init_AdaBins(device=None):
    """
    Legacy function for backward compatibility
    Now initializes modern depth model instead
    """
    logger.warning(
        "init_AdaBins() is deprecated. Use init_depth_model() instead. "
        "Initializing with Depth-Anything-V2 by default."
    )

    from pytti.depth_models import init_depth_model

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    init_depth_model(model_type="depth_anything_v2", model_size="base", device=device)


# For truly legacy code that needs actual AdaBins
class LegacyAdaBinsDepthLoss(MSELoss):
    """
    Original AdaBins-based depth loss
    Kept for strict backward compatibility if needed

    To use: from pytti.LossAug.DepthLossClass_modern import LegacyAdaBinsDepthLoss as DepthLoss
    """

    @torch.no_grad()
    def set_comp(self, pil_image):
        self.comp.set_(LegacyAdaBinsDepthLoss.make_comp(pil_image))
        if self.use_mask and self.mask.shape[-2:] != self.comp.shape[-2:]:
            self.mask.set_(TF.resize(self.mask, self.comp.shape[-2:]))

    def get_loss(self, input, img):
        """Original implementation using AdaBins"""
        from adabins.infer import InferenceHelper

        global _legacy_adabins_helper

        if _legacy_adabins_helper is None:
            with vram_usage_mode("AdaBins"):
                logger.debug("Loading legacy AdaBins...")
                device = input.device
                _legacy_adabins_helper = InferenceHelper(dataset="nyu", device=device)
                logger.debug("AdaBins loaded.")

        height, width = input.shape[-2:]
        max_depth_area = 500000
        image_area = width * height

        if image_area > max_depth_area:
            depth_scale_factor = math.sqrt(max_depth_area / image_area)
            height, width = int(height * depth_scale_factor), int(
                width * depth_scale_factor
            )
            depth_input = TF.resize(
                input, (height, width), interpolation=TF.InterpolationMode.BILINEAR
            )
        else:
            depth_input = input

        _, depth_map = _legacy_adabins_helper.model(depth_input)
        depth_map = F.interpolate(
            depth_map, self.comp.shape[-2:], mode="bilinear", align_corners=True
        )

        return super().get_loss(depth_map, img)

    @classmethod
    @vram_usage_mode("Depth Loss")
    def make_comp(cls, pil_image, device=None):
        """Original AdaBins-based comparison"""
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        depth, _ = cls.get_depth(pil_image, device=device)
        return torch.from_numpy(depth).to(device)

    @staticmethod
    def get_depth(pil_image, device=None):
        """Original AdaBins depth estimation"""
        from adabins.infer import InferenceHelper

        global _legacy_adabins_helper

        if _legacy_adabins_helper is None:
            with vram_usage_mode("AdaBins"):
                if device is None:
                    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                _legacy_adabins_helper = InferenceHelper(dataset="nyu", device=device)

        width, height = pil_image.size
        max_depth_area = 500000
        image_area = width * height

        if image_area > max_depth_area:
            depth_scale_factor = math.sqrt(max_depth_area / image_area)
            depth_input = pil_image.resize(
                (int(width * depth_scale_factor), int(height * depth_scale_factor)),
                Image.LANCZOS,
            )
            depth_resized = True
        else:
            depth_input = pil_image
            depth_resized = False

        gc.collect()
        torch.cuda.empty_cache()
        _, depth_map = _legacy_adabins_helper.predict_pil(depth_input)
        gc.collect()
        torch.cuda.empty_cache()

        return depth_map, depth_resized


# Global legacy AdaBins helper
_legacy_adabins_helper = None
