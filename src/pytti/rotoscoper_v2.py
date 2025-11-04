"""
AI-Powered Rotoscoping for PyTTI (Version 2)
Integrates SAM 2 for automatic video segmentation while preserving PyTTI's workflow

This module extends PyTTI's original rotoscoping with modern AI capabilities:
- SAM 2 for automatic object segmentation and tracking
- Point/box/mask prompting for interactive segmentation
- Temporal consistency across video frames
- Backward compatible with original Rotoscoper

Inspired by ComfyUI's SAM integration but adapted for PyTTI's unique video workflow
"""

from __future__ import annotations

import gc
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Union, Literal
from dataclasses import dataclass

import torch
import numpy as np
from PIL import Image
from loguru import logger

# Import PyTTI's existing rotoscoping infrastructure
from pytti.rotoscoper import (
    RotoscopingOrchestrator,
    ROTOSCOPERS,
    get_frames,
)
from pytti import vram_usage_mode


@dataclass
class SegmentationPrompt:
    """
    Segmentation prompt for SAM 2
    Supports points, boxes, and masks
    """
    # Point prompts: List of (x, y, label) where label is 1 (foreground) or 0 (background)
    points: Optional[List[Tuple[int, int, int]]] = None

    # Box prompt: (x1, y1, x2, y2)
    box: Optional[Tuple[int, int, int, int]] = None

    # Mask prompt: numpy array or tensor
    mask: Optional[Union[np.ndarray, torch.Tensor]] = None

    # Frame index for this prompt
    frame_idx: int = 0


class SAM2Segmenter:
    """
    SAM 2 Video Segmentation
    Handles loading and inference with SAM 2 models
    """

    def __init__(
        self,
        model_size: Literal["tiny", "small", "base", "large"] = "base",
        device: Optional[torch.device] = None,
    ):
        """
        Initialize SAM 2 segmenter

        Args:
            model_size: SAM 2 model size (tiny, small, base, large)
            device: Device to run on
        """
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.device = device
        self.model_size = model_size
        self.model_id = f"sam2_{model_size}"
        self.model = None
        self.predictor = None

        logger.info(f"Initializing SAM 2 ({model_size})")

    def load_model(self):
        """Load SAM 2 model"""
        if self.model is not None:
            return

        logger.info(f"Loading SAM 2 model: {self.model_size}")

        with vram_usage_mode(f"SAM 2 ({self.model_size})"):
            try:
                # Try importing SAM 2
                from sam2.build_sam import build_sam2_video_predictor
                from sam2.sam2_image_predictor import SAM2ImagePredictor

                # Model configs
                model_cfg_map = {
                    "tiny": "sam2_hiera_t.yaml",
                    "small": "sam2_hiera_s.yaml",
                    "base": "sam2_hiera_b+.yaml",
                    "large": "sam2_hiera_l.yaml",
                }

                model_cfg = model_cfg_map[self.model_size]

                # Load video predictor
                from pytti.model_loader import get_model_loader

                loader = get_model_loader(device=self.device)

                # Download model checkpoint
                checkpoint_path = self._download_checkpoint()

                # Build predictor
                self.predictor = build_sam2_video_predictor(
                    model_cfg,
                    checkpoint_path,
                    device=self.device,
                )

                logger.info(f"  SAM 2 {self.model_size} loaded successfully")

            except ImportError as e:
                logger.error(
                    f"SAM 2 not available: {e}\n"
                    "Install with: pip install git+https://github.com/facebookresearch/segment-anything-2.git"
                )
                raise

    def _download_checkpoint(self) -> Path:
        """Download SAM 2 checkpoint"""
        from pytti.model_loader import ModelRegistry, get_model_loader

        loader = get_model_loader()
        model_config = ModelRegistry.SEGMENTATION_MODELS.get(self.model_id)

        if not model_config:
            raise ValueError(f"Unknown SAM 2 model: {self.model_id}")

        checkpoint_path = loader.download_model(model_config)
        return checkpoint_path

    @torch.no_grad()
    def segment_video(
        self,
        frames: List[np.ndarray],
        prompts: List[SegmentationPrompt],
    ) -> Dict[int, np.ndarray]:
        """
        Segment objects in video with temporal tracking

        Args:
            frames: List of video frames as numpy arrays (H, W, 3)
            prompts: List of segmentation prompts (typically for first frame)

        Returns:
            Dictionary mapping frame index to binary mask
        """
        if self.predictor is None:
            self.load_model()

        logger.info(f"Segmenting video with SAM 2 ({len(frames)} frames)")

        # Initialize video predictor with frames
        with vram_usage_mode("SAM 2 Video Segmentation"):
            inference_state = self.predictor.init_state(video_path=None, video=frames)

            # Add prompts
            for prompt in prompts:
                if prompt.points:
                    # Convert points to SAM 2 format
                    points = np.array([[p[0], p[1]] for p in prompt.points])
                    labels = np.array([p[2] for p in prompt.points])

                    self.predictor.add_new_points(
                        inference_state=inference_state,
                        frame_idx=prompt.frame_idx,
                        obj_id=0,  # Single object for now
                        points=points,
                        labels=labels,
                    )

                if prompt.box:
                    # Add box prompt
                    box = np.array(prompt.box)
                    self.predictor.add_new_box(
                        inference_state=inference_state,
                        frame_idx=prompt.frame_idx,
                        obj_id=0,
                        box=box,
                    )

            # Propagate masks through video
            masks_dict = {}

            for frame_idx, object_ids, masks in self.predictor.propagate_in_video(
                inference_state
            ):
                # Extract mask for our object
                if len(masks) > 0:
                    mask = masks[0].cpu().numpy()  # First object
                    masks_dict[frame_idx] = mask

        logger.info(f"  Generated masks for {len(masks_dict)} frames")
        return masks_dict

    @torch.no_grad()
    def segment_image(
        self,
        image: Union[np.ndarray, Image.Image],
        prompt: SegmentationPrompt,
    ) -> np.ndarray:
        """
        Segment single image (for non-video use)

        Args:
            image: Input image
            prompt: Segmentation prompt

        Returns:
            Binary mask as numpy array
        """
        if self.predictor is None:
            self.load_model()

        # Convert PIL to numpy if needed
        if isinstance(image, Image.Image):
            image = np.array(image)

        with vram_usage_mode("SAM 2 Image Segmentation"):
            # Set image
            self.predictor.set_image(image)

            # Apply prompt
            if prompt.points:
                points = np.array([[p[0], p[1]] for p in prompt.points])
                labels = np.array([p[2] for p in prompt.points])

                masks, scores, _ = self.predictor.predict(
                    point_coords=points,
                    point_labels=labels,
                    multimask_output=True,
                )

            elif prompt.box:
                box = np.array(prompt.box)
                masks, scores, _ = self.predictor.predict(
                    box=box,
                    multimask_output=True,
                )

            else:
                raise ValueError("Must provide either points or box prompt")

            # Return best mask (highest score)
            best_mask_idx = np.argmax(scores)
            return masks[best_mask_idx]


class AIRotoscoper:
    """
    AI-Powered Rotoscoper using SAM 2
    Modern replacement for PyTTI's manual Rotoscoper with automatic tracking

    Usage:
        # Automatic segmentation from points
        rotoscoper = AIRotoscoper("video.mp4")
        rotoscoper.segment_with_points(frame_idx=0, points=[(100, 200, 1), (150, 250, 1)])
        rotoscoper.apply_to_target(target_image_guide)

        # Or use as context manager
        with AIRotoscoper("video.mp4") as rotoscoper:
            rotoscoper.auto_segment(initial_mask=mask)
    """

    def __init__(
        self,
        video_path: Union[str, Path],
        target=None,
        model_size: Literal["tiny", "small", "base", "large"] = "base",
        inverted: bool = False,
        device: Optional[torch.device] = None,
    ):
        """
        Initialize AI rotoscoper

        Args:
            video_path: Path to video file
            target: Optional target image guide to apply masks to
            model_size: SAM 2 model size
            inverted: Whether to invert the mask
            device: Device to run on
        """
        # Handle inverted flag in path (PyTTI compatibility)
        if isinstance(video_path, str) and video_path.startswith("-"):
            video_path = video_path[1:]
            inverted = True

        self.video_path = Path(video_path)
        self.target = target
        self.inverted = inverted
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load video frames (using PyTTI's existing function)
        logger.info(f"Loading video: {self.video_path}")
        self.frames_reader = get_frames(str(self.video_path))
        self.num_frames = self.frames_reader._meta["nframes"]
        logger.info(f"  Loaded {self.num_frames} frames")

        # Initialize SAM 2
        self.segmenter = SAM2Segmenter(model_size=model_size, device=self.device)

        # Storage for generated masks
        self.masks: Dict[int, np.ndarray] = {}

        # Register with global rotoscoper orchestrator (PyTTI compatibility)
        ROTOSCOPERS.add(self)

    def segment_with_points(
        self,
        frame_idx: int,
        points: List[Tuple[int, int, int]],
        auto_propagate: bool = True,
    ):
        """
        Segment object using point prompts and track through video

        Args:
            frame_idx: Frame index to place points on
            points: List of (x, y, label) tuples where label is 1 (fg) or 0 (bg)
            auto_propagate: Whether to automatically propagate to all frames
        """
        logger.info(f"Segmenting with {len(points)} point prompts at frame {frame_idx}")

        # Create prompt
        prompt = SegmentationPrompt(
            points=points,
            frame_idx=frame_idx,
        )

        if auto_propagate:
            # Load all frames
            frames = [self.frames_reader.get_data(i) for i in range(self.num_frames)]

            # Segment entire video
            self.masks = self.segmenter.segment_video(frames, [prompt])
        else:
            # Segment single frame only
            frame = self.frames_reader.get_data(frame_idx)
            mask = self.segmenter.segment_image(frame, prompt)
            self.masks[frame_idx] = mask

        logger.info(f"  Generated masks for {len(self.masks)} frames")

    def segment_with_box(
        self,
        frame_idx: int,
        box: Tuple[int, int, int, int],
        auto_propagate: bool = True,
    ):
        """
        Segment object using box prompt and track through video

        Args:
            frame_idx: Frame index to place box on
            box: Bounding box as (x1, y1, x2, y2)
            auto_propagate: Whether to automatically propagate to all frames
        """
        logger.info(f"Segmenting with box prompt at frame {frame_idx}")

        prompt = SegmentationPrompt(
            box=box,
            frame_idx=frame_idx,
        )

        if auto_propagate:
            frames = [self.frames_reader.get_data(i) for i in range(self.num_frames)]
            self.masks = self.segmenter.segment_video(frames, [prompt])
        else:
            frame = self.frames_reader.get_data(frame_idx)
            mask = self.segmenter.segment_image(frame, prompt)
            self.masks[frame_idx] = mask

        logger.info(f"  Generated masks for {len(self.masks)} frames")

    def auto_segment_from_mask(self, initial_mask: Union[np.ndarray, Image.Image], frame_idx: int = 0):
        """
        Automatically track an object from an initial mask

        Args:
            initial_mask: Initial binary mask (2D array or PIL image)
            frame_idx: Frame index of initial mask
        """
        logger.info(f"Auto-segmenting from initial mask at frame {frame_idx}")

        # Convert mask to numpy if PIL
        if isinstance(initial_mask, Image.Image):
            initial_mask = np.array(initial_mask.convert("L")) > 128

        # Extract points from mask (sample from center of mask region)
        y_coords, x_coords = np.where(initial_mask)
        if len(y_coords) == 0:
            raise ValueError("Initial mask is empty")

        # Sample some points from the masked region
        num_points = min(10, len(y_coords))
        indices = np.random.choice(len(y_coords), num_points, replace=False)
        points = [(int(x_coords[i]), int(y_coords[i]), 1) for i in indices]

        # Use point-based segmentation
        self.segment_with_points(frame_idx, points, auto_propagate=True)

    def update(self, frame_n: int):
        """
        Update mask for specific frame (PyTTI Rotoscoper interface)

        Args:
            frame_n: Frame number to update
        """
        if self.target is None:
            return

        if frame_n not in self.masks:
            # Generate mask if not available
            logger.warning(f"Frame {frame_n} not in pre-computed masks, skipping")
            return

        # Get mask for this frame
        mask_array = self.masks[frame_n]

        # Convert to PIL image
        if mask_array.dtype != np.uint8:
            mask_array = (mask_array * 255).astype(np.uint8)

        mask_pil = Image.fromarray(mask_array).convert("L")

        # Apply to target (PyTTI's interface)
        self.target.set_mask(mask_pil, self.inverted)

    def apply_to_target(self, target):
        """
        Apply this rotoscoper to a target image guide

        Args:
            target: Target image guide to apply masks to
        """
        self.target = target

    def get_mask_for_frame(self, frame_idx: int) -> Optional[Image.Image]:
        """
        Get mask as PIL Image for specific frame

        Args:
            frame_idx: Frame index

        Returns:
            PIL Image mask or None if not available
        """
        if frame_idx not in self.masks:
            return None

        mask_array = self.masks[frame_idx]
        if mask_array.dtype != np.uint8:
            mask_array = (mask_array * 255).astype(np.uint8)

        return Image.fromarray(mask_array).convert("L")

    def save_masks(self, output_dir: Union[str, Path]):
        """
        Save all masks to directory

        Args:
            output_dir: Directory to save masks to
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving {len(self.masks)} masks to {output_dir}")

        for frame_idx, mask in self.masks.items():
            mask_pil = self.get_mask_for_frame(frame_idx)
            if mask_pil:
                mask_pil.save(output_dir / f"mask_{frame_idx:04d}.png")

        logger.info("  Masks saved")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup"""
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        # Clear masks from memory
        self.masks.clear()

        # Clear GPU cache
        if self.device.type == "cuda":
            torch.cuda.empty_cache()


# Convenience function for quick rotoscoping
def quick_rotoscope(
    video_path: str,
    points: List[Tuple[int, int, int]],
    frame_idx: int = 0,
    model_size: str = "base",
    save_masks: bool = True,
    output_dir: Optional[str] = None,
) -> AIRotoscoper:
    """
    Quick rotoscoping helper function

    Args:
        video_path: Path to video
        points: Point prompts for segmentation
        frame_idx: Frame to place points on
        model_size: SAM 2 model size
        save_masks: Whether to save masks
        output_dir: Where to save masks

    Returns:
        AIRotoscoper instance with generated masks
    """
    rotoscoper = AIRotoscoper(video_path, model_size=model_size)
    rotoscoper.segment_with_points(frame_idx, points)

    if save_masks:
        if output_dir is None:
            output_dir = Path(video_path).parent / "masks"
        rotoscoper.save_masks(output_dir)

    return rotoscoper


# Export main classes
__all__ = [
    "SAM2Segmenter",
    "AIRotoscoper",
    "SegmentationPrompt",
    "quick_rotoscope",
]
