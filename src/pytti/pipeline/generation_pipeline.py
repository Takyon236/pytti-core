"""
Generation Pipeline for PyTTI

A clean, testable pipeline that separates the generation process into distinct steps.
Each step is isolated, making it easy to test, debug, and maintain.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, TypedDict
from dataclasses import dataclass, field

import torch
import numpy as np
from PIL import Image
from loguru import logger

from pytti.image_models.diffusion import StableDiffusionImage, FluxImage, DifferentiableImage
from pytti.Perceptor.Embedder import HDMultiClipEmbedder
from pytti.Perceptor.Prompt import parse_prompt
from pytti.managers import ClipManager
from pytti.validation import ConfigValidator
from pytti.exceptions import (
    ModelLoadError,
    VRAMError,
    GenerationError,
    PromptParseError,
    FileIOError,
)


class GenerationConfig(TypedDict, total=False):
    """Type definition for generation configuration."""

    # Required fields
    prompt: str
    width: int
    height: int
    steps_per_scene: int

    # Model selection
    diffusion_model: str
    clip_model: str

    # Generation parameters
    learning_rate: float
    cutouts: int
    cut_pow: float
    ema_val: float
    seed: int

    # Output settings
    file_namespace: str
    save_every: int


@dataclass
class GenerationState:
    """Holds the state during generation."""

    # Models
    img_model: Optional[DifferentiableImage] = None
    clip_embedder: Optional[HDMultiClipEmbedder] = None
    prompt_obj: Optional[Any] = None

    # Paths
    output_dir: Optional[Path] = None
    output_path: Optional[Path] = None

    # Progress
    current_step: int = 0
    total_steps: int = 0
    failed_steps: int = 0

    # Results
    result_image: Optional[Image.Image] = None

    # Timing
    start_time: float = field(default_factory=time.time)
    step_times: list[float] = field(default_factory=list)


class GenerationPipeline:
    """
    Clean generation pipeline with separated concerns.

    Each step is isolated for better testing and maintainability.

    Usage:
        >>> pipeline = GenerationPipeline(config, device, progress_callback)
        >>> result_image, output_path = pipeline.run()
    """

    def __init__(
        self,
        config: GenerationConfig,
        device: torch.device,
        progress_callback: Optional[Callable[[tuple[int, int], str], None]] = None,
    ):
        """
        Initialize generation pipeline.

        Args:
            config: Generation configuration
            device: PyTorch device (cuda or cpu)
            progress_callback: Optional callback for progress updates
        """
        self.config = config
        self.device = device
        self.progress_callback = progress_callback
        self.state = GenerationState()

        # Configuration
        self.max_failed_steps = 10  # Abort if too many failures

    def run(self) -> tuple[Image.Image, Path]:
        """
        Run the complete generation pipeline.

        Returns:
            Tuple of (result_image, output_path)

        Raises:
            Various PyTTI exceptions for different failure modes
        """
        logger.info("=" * 60)
        logger.info("🚀 STARTING GENERATION PIPELINE")
        logger.info("=" * 60)

        # Step 0: Validate configuration
        self._validate_config()

        # Step 1: Setup output directory
        self._setup_output_directory()

        # Step 2: Initialize diffusion model
        self._initialize_diffusion_model()

        # Step 3: Initialize random latent
        self._initialize_random_latent()

        # Step 4: Initialize CLIP
        self._initialize_clip()

        # Step 5: Parse prompt
        self._parse_prompt()

        # Step 6: Run optimization loop
        self._run_optimization()

        # Step 7: Finalize and save
        self._finalize_generation()

        logger.info("=" * 60)
        logger.info("✅ GENERATION PIPELINE COMPLETE")
        logger.info(f"   Time: {time.time() - self.state.start_time:.1f}s")
        logger.info(f"   Output: {self.state.output_path}")
        logger.info("=" * 60)

        return self.state.result_image, self.state.output_path

    # =========================================================================
    # Pipeline Steps
    # =========================================================================

    def _validate_config(self) -> None:
        """Step 0: Validate configuration."""
        logger.info("📋 Step 0: Validating configuration...")

        try:
            ConfigValidator.validate_and_raise(self.config)
            logger.info("✓ Configuration validated")
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    def _setup_output_directory(self) -> None:
        """Step 1: Setup output directory."""
        logger.info("📁 Step 1: Setting up output directory...")

        try:
            self.state.output_dir = Path("outputs") / self.config["file_namespace"]
            self.state.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Output directory: {self.state.output_dir}")
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")
            raise FileIOError("create", str(self.state.output_dir), e)

    def _initialize_diffusion_model(self) -> None:
        """Step 2: Initialize diffusion model."""
        logger.info(f"🎨 Step 2: Loading diffusion model '{self.config['diffusion_model']}'...")

        try:
            # Map UI model names to model IDs
            model_map = {
                "Stable Diffusion XL": "sdxl",
                "Flux Schnell": "flux_schnell",
                "Flux Dev": "flux_dev",
                "Stable Diffusion 1.5": "sd_1.5",
            }

            model_id = model_map.get(self.config["diffusion_model"], "sdxl")

            # Create appropriate model type
            if "Flux" in self.config["diffusion_model"]:
                self.state.img_model = FluxImage(
                    width=self.config["width"],
                    height=self.config["height"],
                    model_id=model_id,
                    ema_val=self.config["ema_val"],
                    device=self.device,
                )
            else:
                self.state.img_model = StableDiffusionImage(
                    width=self.config["width"],
                    height=self.config["height"],
                    model_id=model_id,
                    ema_val=self.config["ema_val"],
                    device=self.device,
                )

            logger.info("✓ Diffusion model loaded")

        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"VRAM error loading model: {e}")
            raise VRAMError()
        except Exception as e:
            logger.error(f"Failed to load diffusion model: {e}")
            raise ModelLoadError(self.config["diffusion_model"], e)

    def _initialize_random_latent(self) -> None:
        """Step 3: Initialize random latent."""
        logger.info("🎲 Step 3: Initializing random latent...")

        # Set seed if specified
        if self.config["seed"] >= 0:
            torch.manual_seed(self.config["seed"])
            np.random.seed(self.config["seed"])
            logger.info(f"   Using seed: {self.config['seed']}")

        self.state.img_model.encode_random()
        logger.info("✓ Random latent initialized")

    def _initialize_clip(self) -> None:
        """Step 4: Initialize CLIP perceptors."""
        logger.info("👁️  Step 4: Loading CLIP model...")

        try:
            clip_manager = ClipManager.get_instance()

            # Get CLIP model from config
            clip_model_name = self.config.get("clip_model", "ViT-B/32")

            # Map UI names to model names
            clip_model_map = {
                "ViT-B/32 (Fast)": "ViT-B/32",
                "ViT-B/16 (Balanced)": "ViT-B/16",
                "ViT-L/14 (Quality)": "ViT-L/14",
                "SigLIP (Recommended)": "ViT-B/16",
            }

            clip_model = clip_model_map.get(clip_model_name, clip_model_name)
            clip_models = [clip_model]

            clip_manager.initialize(clip_models, device=self.device)
            logger.info(f"✓ CLIP model loaded: {clip_model}")

        except Exception as e:
            logger.error(f"Failed to load CLIP: {e}")
            raise ModelLoadError(f"CLIP ({clip_model})", e)

        # Initialize CLIP embedder
        try:
            self.state.clip_embedder = HDMultiClipEmbedder(
                cutn=self.config["cutouts"],
                cut_pow=self.config["cut_pow"],
                device=self.device,
            )
            logger.info("✓ CLIP embedder initialized")
        except Exception as e:
            logger.error(f"Failed to create CLIP embedder: {e}")
            raise ModelLoadError("CLIP Embedder", e)

    def _parse_prompt(self) -> None:
        """Step 5: Parse prompt."""
        logger.info(f"📝 Step 5: Parsing prompt '{self.config['prompt'][:50]}...'")

        try:
            self.state.prompt_obj = parse_prompt(
                self.state.clip_embedder,
                self.config["prompt"]
            )
            logger.info("✓ Prompt parsed successfully")
        except Exception as e:
            logger.error(f"Failed to parse prompt: {e}")
            raise PromptParseError(self.config["prompt"], e)

    def _run_optimization(self) -> None:
        """Step 6: Run iterative optimization loop."""
        logger.info(f"🔄 Step 6: Starting optimization ({self.config['steps_per_scene']} steps)...")

        learning_rate = self.config["learning_rate"]
        self.state.total_steps = self.config["steps_per_scene"]

        for step in range(self.state.total_steps):
            step_start = time.time()

            # Check failure threshold
            if self.state.failed_steps >= self.max_failed_steps:
                raise GenerationError(
                    step,
                    Exception(f"Too many failures: {self.state.failed_steps}")
                )

            # Update progress
            self.state.current_step = step + 1
            if self.progress_callback:
                self.progress_callback(
                    (step + 1, self.state.total_steps),
                    f"Step {step + 1}/{self.state.total_steps}"
                )

            # Run optimization step
            try:
                self._optimization_step(step, learning_rate)
                self.state.failed_steps = 0  # Reset on success

            except torch.cuda.OutOfMemoryError as e:
                logger.error(f"VRAM error at step {step}: {e}")
                raise VRAMError()

            except Exception as e:
                logger.error(f"Error in step {step}: {e}")
                self.state.failed_steps += 1

                if self.state.failed_steps < self.max_failed_steps:
                    logger.warning(f"Continuing... ({self.state.failed_steps}/{self.max_failed_steps} failures)")
                    continue
                else:
                    raise GenerationError(step, e)

            # Track timing
            step_time = time.time() - step_start
            self.state.step_times.append(step_time)

        logger.info(f"✓ Optimization complete ({self.state.total_steps} steps)")

    def _optimization_step(self, step: int, learning_rate: float) -> None:
        """Execute a single optimization step."""
        # Get current latent
        current_latent = self.state.img_model.get_image_tensor()

        # Decode for CLIP evaluation
        with torch.no_grad():
            current_image = self.state.img_model.decode(current_latent)

        # Compute CLIP loss
        clip_loss = self.state.prompt_obj.compute_loss(current_image)

        # Compute gradients
        if current_latent.grad is not None:
            current_latent.grad.zero_()

        clip_loss.backward()

        # Update latent with gradient descent
        with torch.no_grad():
            if current_latent.grad is not None:
                current_latent -= learning_rate * current_latent.grad

            # Apply EMA smoothing
            self.state.img_model.update_ema()

        # Save intermediate results
        if (step + 1) % self.config["save_every"] == 0:
            self._save_intermediate(step)

    def _save_intermediate(self, step: int) -> None:
        """Save intermediate result."""
        try:
            intermediate_path = (
                self.state.output_dir /
                f"{self.config['file_namespace']}_step_{step+1:04d}.png"
            )
            intermediate_image = self.state.img_model.decode_image()
            intermediate_image.save(intermediate_path)
            logger.info(f"💾 Saved: {intermediate_path.name}")
        except Exception as e:
            logger.warning(f"Failed to save intermediate: {e}")
            # Don't abort generation for save failures

    def _finalize_generation(self) -> None:
        """Step 7: Finalize and save final image."""
        logger.info("🎨 Step 7: Finalizing generation...")

        # Decode final image
        try:
            self.state.result_image = self.state.img_model.decode_image()
            logger.info("✓ Final image decoded")
        except Exception as e:
            logger.error(f"Failed to decode final image: {e}")
            raise GenerationError(self.state.total_steps, e)

        # Save final result
        try:
            self.state.output_path = (
                self.state.output_dir /
                f"{self.config['file_namespace']}_final.png"
            )
            self.state.result_image.save(self.state.output_path)
            logger.info(f"✅ Saved final result: {self.state.output_path}")
        except Exception as e:
            logger.error(f"Failed to save final image: {e}")
            raise FileIOError("save", str(self.state.output_path), e)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_eta(self) -> Optional[str]:
        """
        Calculate estimated time remaining.

        Returns:
            Formatted ETA string or None if not enough data
        """
        if len(self.state.step_times) < 3:
            return None

        # Average of last 10 steps
        recent_times = self.state.step_times[-10:]
        avg_time = sum(recent_times) / len(recent_times)

        remaining_steps = self.state.total_steps - self.state.current_step
        eta_seconds = avg_time * remaining_steps

        if eta_seconds < 60:
            return f"{int(eta_seconds)}s"
        elif eta_seconds < 3600:
            return f"{int(eta_seconds / 60)}m {int(eta_seconds % 60)}s"
        else:
            hours = int(eta_seconds / 3600)
            minutes = int((eta_seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def get_progress_percent(self) -> float:
        """Get progress percentage."""
        if self.state.total_steps == 0:
            return 0.0
        return (self.state.current_step / self.state.total_steps) * 100
