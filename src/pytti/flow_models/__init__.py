"""
Modern Optical Flow Models for PyTTI
Replaces legacy GMA with state-of-the-art flow estimation

Supported models:
- CoTracker (Meta 2024) - Long-term point tracking, perfect for rotoscoping
- RAFT (updated) - Fast and accurate optical flow
- GMA (legacy) - For backward compatibility

Maintains compatibility with PyTTI's optical flow loss system
"""

from __future__ import annotations

from typing import Optional, Tuple, Union, Literal
from pathlib import Path

import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from torchvision.transforms import functional as TF
from loguru import logger

from pytti import vram_usage_mode


class BaseFlowEstimator:
    """
    Base class for optical flow estimators
    Provides unified interface for PyTTI's flow system
    """

    def __init__(self, device: Optional[torch.device] = None):
        """Initialize flow estimator"""
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.device = device
        self.model = None

    @torch.no_grad()
    def estimate_flow(
        self,
        image1: Union[Image.Image, torch.Tensor],
        image2: Union[Image.Image, torch.Tensor],
    ) -> torch.Tensor:
        """
        Estimate optical flow between two images

        Args:
            image1: First image (source)
            image2: Second image (target)

        Returns:
            Flow tensor of shape (1, 2, H, W)
        """
        raise NotImplementedError("Subclass must implement estimate_flow")

    def load_model(self):
        """Load the flow estimation model"""
        raise NotImplementedError("Subclass must implement load_model")


class CoTrackerFlow(BaseFlowEstimator):
    """
    CoTracker - Long-term point tracking (Meta 2024)
    Perfect for PyTTI's rotoscoping and temporal coherence

    Paper: https://arxiv.org/abs/2307.07635
    Repo: https://github.com/facebookresearch/co-tracker
    """

    def __init__(
        self,
        model_size: Literal["stride_4_wind_8", "stride_8_wind_16"] = "stride_4_wind_8",
        device: Optional[torch.device] = None,
    ):
        """
        Initialize CoTracker

        Args:
            model_size: Model variant (stride_4_wind_8 is more accurate)
            device: Device to run on
        """
        super().__init__(device)
        self.model_size = model_size

    def load_model(self):
        """Load CoTracker model"""
        if self.model is not None:
            return

        logger.info(f"Loading CoTracker ({self.model_size})")

        with vram_usage_mode("CoTracker"):
            try:
                from cotracker.predictor import CoTrackerPredictor

                self.model = CoTrackerPredictor(
                    checkpoint=f"cotracker_{self.model_size}.pth"
                )
                self.model = self.model.to(self.device)
                self.model.eval()

                logger.info("  CoTracker loaded successfully")

            except ImportError:
                logger.error(
                    "CoTracker not available. Install with:\n"
                    "  pip install git+https://github.com/facebookresearch/co-tracker"
                )
                raise

    @torch.no_grad()
    def estimate_flow(
        self,
        image1: Union[Image.Image, torch.Tensor],
        image2: Union[Image.Image, torch.Tensor],
    ) -> torch.Tensor:
        """
        Estimate flow using CoTracker
        Uses dense point tracking internally
        """
        if self.model is None:
            self.load_model()

        # Convert to tensors
        if isinstance(image1, Image.Image):
            image1 = TF.to_tensor(image1).unsqueeze(0)
        if isinstance(image2, Image.Image):
            image2 = TF.to_tensor(image2).unsqueeze(0)

        image1 = image1.to(self.device)
        image2 = image2.to(self.device)

        # Stack into video
        video = torch.cat([image1, image2], dim=0).unsqueeze(0)  # (1, 2, C, H, W)

        with vram_usage_mode("CoTracker Flow Estimation"):
            # Use CoTracker to track points
            # Sample grid of points
            H, W = image1.shape[-2:]
            grid_step = 8
            y_coords = torch.arange(0, H, grid_step, device=self.device)
            x_coords = torch.arange(0, W, grid_step, device=self.device)
            yy, xx = torch.meshgrid(y_coords, x_coords, indexing='ij')
            queries = torch.stack([
                torch.zeros_like(xx.flatten()),  # Frame 0
                xx.flatten(),
                yy.flatten(),
            ], dim=1).float()  # (N, 3) - (t, x, y)

            # Track points through video
            pred_tracks, pred_visibility = self.model(video, queries=queries.unsqueeze(0))

            # Convert tracks to flow
            # pred_tracks: (B, T, N, 2)
            tracks_frame0 = pred_tracks[0, 0]  # (N, 2)
            tracks_frame1 = pred_tracks[0, 1]  # (N, 2)

            flow_vectors = tracks_frame1 - tracks_frame0  # (N, 2)

            # Reshape to grid and interpolate to full resolution
            grid_h = len(y_coords)
            grid_w = len(x_coords)

            flow_grid = flow_vectors.reshape(grid_h, grid_w, 2)  # (H', W', 2)
            flow_grid = flow_grid.permute(2, 0, 1).unsqueeze(0)  # (1, 2, H', W')

            # Interpolate to original resolution
            flow = F.interpolate(
                flow_grid,
                size=(H, W),
                mode='bilinear',
                align_corners=True
            )

        return flow

    @torch.no_grad()
    def track_video(
        self,
        video_frames: torch.Tensor,
        queries: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Track points through entire video (CoTracker's strength!)

        Args:
            video_frames: Video tensor (B, T, C, H, W)
            queries: Optional point queries (B, N, 3) as (t, x, y)

        Returns:
            Tuple of (tracks, visibility)
                tracks: (B, T, N, 2) - tracked point locations
                visibility: (B, T, N) - visibility flags
        """
        if self.model is None:
            self.load_model()

        if queries is None:
            # Auto-generate dense grid of queries
            H, W = video_frames.shape[-2:]
            grid_step = 8
            y_coords = torch.arange(0, H, grid_step, device=self.device)
            x_coords = torch.arange(0, W, grid_step, device=self.device)
            yy, xx = torch.meshgrid(y_coords, x_coords, indexing='ij')
            queries = torch.stack([
                torch.zeros_like(xx.flatten()),
                xx.flatten(),
                yy.flatten(),
            ], dim=1).float().unsqueeze(0)

        with vram_usage_mode("CoTracker Video Tracking"):
            tracks, visibility = self.model(video_frames, queries=queries)

        return tracks, visibility


class RAFTFlow(BaseFlowEstimator):
    """
    RAFT - Recurrent All-Pairs Field Transforms
    Fast and accurate optical flow

    Paper: https://arxiv.org/abs/2003.12039
    Repo: https://github.com/princeton-vl/RAFT
    """

    def __init__(self, device: Optional[torch.device] = None):
        """Initialize RAFT"""
        super().__init__(device)

    def load_model(self):
        """Load RAFT model"""
        if self.model is not None:
            return

        logger.info("Loading RAFT optical flow model")

        with vram_usage_mode("RAFT"):
            try:
                # Try loading from torchvision (if available)
                from torchvision.models.optical_flow import raft_large

                self.model = raft_large(pretrained=True, progress=True)
                self.model = self.model.to(self.device)
                self.model.eval()

                logger.info("  RAFT loaded from torchvision")

            except (ImportError, AttributeError):
                # Fallback to direct RAFT implementation
                try:
                    import sys
                    # Add RAFT to path
                    # This would need RAFT installed as per their repo
                    from raft import RAFT as RAFTModel
                    import argparse

                    args = argparse.Namespace()
                    args.model = "raft-things.pth"
                    args.small = False
                    args.mixed_precision = False

                    self.model = RAFTModel(args)
                    self.model = self.model.to(self.device)
                    self.model.eval()

                    logger.info("  RAFT loaded from direct implementation")

                except ImportError:
                    logger.error(
                        "RAFT not available. Install with:\n"
                        "  pip install git+https://github.com/princeton-vl/RAFT"
                    )
                    raise

    @torch.no_grad()
    def estimate_flow(
        self,
        image1: Union[Image.Image, torch.Tensor],
        image2: Union[Image.Image, torch.Tensor],
    ) -> torch.Tensor:
        """Estimate flow using RAFT"""
        if self.model is None:
            self.load_model()

        # Convert to tensors
        if isinstance(image1, Image.Image):
            image1 = TF.to_tensor(image1).unsqueeze(0)
        if isinstance(image2, Image.Image):
            image2 = TF.to_tensor(image2).unsqueeze(0)

        image1 = image1.to(self.device)
        image2 = image2.to(self.device)

        # Normalize to [-1, 1] (RAFT expects this)
        image1 = image1 * 2 - 1
        image2 = image2 * 2 - 1

        with vram_usage_mode("RAFT Flow Estimation"):
            # RAFT returns list of flow predictions (multi-scale)
            flow_predictions = self.model(image1, image2)

            # Use final (most refined) prediction
            if isinstance(flow_predictions, list):
                flow = flow_predictions[-1]
            else:
                flow = flow_predictions

        return flow


# Legacy GMA support (for backward compatibility)
class GMAFlow(BaseFlowEstimator):
    """
    GMA - Legacy optical flow model from original PyTTI
    Kept for backward compatibility
    """

    def __init__(self, checkpoint_path: Optional[str] = None, device: Optional[torch.device] = None):
        """Initialize GMA"""
        super().__init__(device)
        self.checkpoint_path = checkpoint_path

    def load_model(self):
        """Load GMA model (legacy)"""
        if self.model is None:
            logger.info("Loading legacy GMA optical flow model")
            # Delegate to existing PyTTI GMA loader
            from pytti.LossAug.OpticalFlowLossClass import init_GMA
            init_GMA(checkpoint_path=self.checkpoint_path, device=self.device)

    @torch.no_grad()
    def estimate_flow(
        self,
        image1: Union[Image.Image, torch.Tensor],
        image2: Union[Image.Image, torch.Tensor],
    ) -> torch.Tensor:
        """Estimate flow using legacy GMA"""
        from pytti.LossAug.OpticalFlowLossClass import OpticalFlowLoss
        return OpticalFlowLoss.get_flow(image1, image2, device=self.device)


# Global flow estimator instance
_global_flow_estimator: Optional[BaseFlowEstimator] = None


def init_flow_model(
    model_type: Literal["cotracker", "raft", "gma"] = "cotracker",
    device: Optional[torch.device] = None,
    **kwargs,
):
    """
    Initialize optical flow model
    Replaces GMA with modern alternatives

    Args:
        model_type: Type of flow model (cotracker, raft, gma)
        device: Device to run on
        **kwargs: Additional model-specific arguments
    """
    global _global_flow_estimator

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if model_type == "cotracker":
        _global_flow_estimator = CoTrackerFlow(device=device, **kwargs)
    elif model_type == "raft":
        _global_flow_estimator = RAFTFlow(device=device, **kwargs)
    elif model_type == "gma":
        _global_flow_estimator = GMAFlow(device=device, **kwargs)
    else:
        raise ValueError(f"Unknown flow model type: {model_type}")

    # Preload the model
    _global_flow_estimator.load_model()


def get_flow_estimator() -> BaseFlowEstimator:
    """Get the global flow estimator instance"""
    global _global_flow_estimator

    if _global_flow_estimator is None:
        # Initialize with default (CoTracker)
        init_flow_model()

    return _global_flow_estimator


def estimate_flow(
    image1: Union[Image.Image, torch.Tensor],
    image2: Union[Image.Image, torch.Tensor],
    model_type: Optional[str] = None,
) -> torch.Tensor:
    """
    Convenience function to estimate optical flow

    Args:
        image1: First image
        image2: Second image
        model_type: Optional model type to use

    Returns:
        Flow tensor
    """
    if model_type and _global_flow_estimator is None:
        init_flow_model(model_type=model_type)

    estimator = get_flow_estimator()
    return estimator.estimate_flow(image1, image2)


# Export main classes and functions
__all__ = [
    "BaseFlowEstimator",
    "CoTrackerFlow",
    "RAFTFlow",
    "GMAFlow",
    "init_flow_model",
    "get_flow_estimator",
    "estimate_flow",
]
