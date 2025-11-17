"""
Modern Model Loader Infrastructure
Inspired by ComfyUI's clean model management while preserving PyTTI's unique approach

This module provides a unified interface for loading various AI models:
- Diffusion models (Stable Diffusion, SDXL, Flux)
- Depth estimation (Depth-Anything-V2, Marigold, ZoeDepth)
- Segmentation (SAM 2)
- Optical flow (CoTracker, RAFT)
- CLIP variants (OpenCLIP, SigLIP, EVA-CLIP)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Union, Any, Literal
from dataclasses import dataclass
from enum import Enum

import torch
from loguru import logger
from huggingface_hub import hf_hub_download, snapshot_download

# PyTTI's existing VRAM tools
from pytti import vram_usage_mode

# Disable xformers if it's broken/incompatible
# This must happen before any diffusers imports
try:
    import xformers.ops
    logger.debug("xformers is available")
except Exception as e:
    logger.warning(f"xformers is unavailable or incompatible with current PyTorch version")
    logger.warning(f"  Error: {str(e)[:100]}")
    logger.info("Attempting to disable xformers for diffusers...")

    # Mock xformers to prevent diffusers from trying to use it
    import sys
    from types import ModuleType

    # Create a fake xformers module that doesn't crash
    fake_xformers = ModuleType('xformers')
    fake_xformers_ops = ModuleType('xformers.ops')
    fake_xformers.ops = fake_xformers_ops

    sys.modules['xformers'] = fake_xformers
    sys.modules['xformers.ops'] = fake_xformers_ops

    logger.info("✓ Created xformers stub to prevent import errors")
    logger.info("💡 To fix this permanently, run: pip install xformers --force-reinstall")


class ModelType(Enum):
    """Enumeration of supported model types"""
    DIFFUSION = "diffusion"
    DEPTH = "depth"
    SEGMENTATION = "segmentation"
    FLOW = "flow"
    CLIP = "clip"
    VQGAN = "vqgan"  # Legacy support


@dataclass
class ModelConfig:
    """
    Configuration for a model
    Similar to ComfyUI's model config but adapted for PyTTI
    """
    name: str
    type: ModelType
    repo_id: str
    filename: Optional[str] = None
    subfolder: Optional[str] = None
    local_path: Optional[Path] = None
    requires_auth: bool = False
    fp16: bool = True  # Use half precision by default

    def __post_init__(self):
        if self.local_path and isinstance(self.local_path, str):
            self.local_path = Path(self.local_path)


class ModelRegistry:
    """
    Central registry of available models
    Inspired by ComfyUI's model database approach
    """

    # Diffusion Models (Main image generation)
    DIFFUSION_MODELS = {
        # Stable Diffusion Family
        "sd_1.5": ModelConfig(
            name="Stable Diffusion 1.5",
            type=ModelType.DIFFUSION,
            repo_id="runwayml/stable-diffusion-v1-5",
        ),
        "sdxl": ModelConfig(
            name="Stable Diffusion XL",
            type=ModelType.DIFFUSION,
            repo_id="stabilityai/stable-diffusion-xl-base-1.0",
        ),
        "sdxl_turbo": ModelConfig(
            name="SDXL Turbo",
            type=ModelType.DIFFUSION,
            repo_id="stabilityai/sdxl-turbo",
        ),
        "sd3.5": ModelConfig(
            name="Stable Diffusion 3.5",
            type=ModelType.DIFFUSION,
            repo_id="stabilityai/stable-diffusion-3.5-large",
            requires_auth=True,
        ),

        # Flux Family
        "flux_schnell": ModelConfig(
            name="Flux Schnell",
            type=ModelType.DIFFUSION,
            repo_id="black-forest-labs/FLUX.1-schnell",
        ),
        "flux_dev": ModelConfig(
            name="Flux Dev",
            type=ModelType.DIFFUSION,
            repo_id="black-forest-labs/FLUX.1-dev",
            requires_auth=True,
        ),
    }

    # Depth Estimation Models
    DEPTH_MODELS = {
        "depth_anything_v2_small": ModelConfig(
            name="Depth Anything V2 Small",
            type=ModelType.DEPTH,
            repo_id="depth-anything/Depth-Anything-V2-Small",
        ),
        "depth_anything_v2_base": ModelConfig(
            name="Depth Anything V2 Base",
            type=ModelType.DEPTH,
            repo_id="depth-anything/Depth-Anything-V2-Base",
        ),
        "depth_anything_v2_large": ModelConfig(
            name="Depth Anything V2 Large",
            type=ModelType.DEPTH,
            repo_id="depth-anything/Depth-Anything-V2-Large",
        ),
        "marigold": ModelConfig(
            name="Marigold Depth",
            type=ModelType.DEPTH,
            repo_id="prs-eth/marigold-v1-0",
        ),
        "zoedepth": ModelConfig(
            name="ZoeDepth",
            type=ModelType.DEPTH,
            repo_id="Intel/zoedepth",
        ),
    }

    # Segmentation Models
    SEGMENTATION_MODELS = {
        "sam2_tiny": ModelConfig(
            name="SAM 2 Tiny",
            type=ModelType.SEGMENTATION,
            repo_id="facebook/sam2-hiera-tiny",
        ),
        "sam2_small": ModelConfig(
            name="SAM 2 Small",
            type=ModelType.SEGMENTATION,
            repo_id="facebook/sam2-hiera-small",
        ),
        "sam2_base": ModelConfig(
            name="SAM 2 Base",
            type=ModelType.SEGMENTATION,
            repo_id="facebook/sam2-hiera-base-plus",
        ),
        "sam2_large": ModelConfig(
            name="SAM 2 Large",
            type=ModelType.SEGMENTATION,
            repo_id="facebook/sam2-hiera-large",
        ),
    }

    # Optical Flow Models
    FLOW_MODELS = {
        "cotracker": ModelConfig(
            name="CoTracker",
            type=ModelType.FLOW,
            repo_id="facebook/cotracker",
        ),
        "raft": ModelConfig(
            name="RAFT",
            type=ModelType.FLOW,
            repo_id="princeton-vl/RAFT",
        ),
    }

    # CLIP & Vision-Language Models
    CLIP_MODELS = {
        "clip_vit_b32": ModelConfig(
            name="CLIP ViT-B/32",
            type=ModelType.CLIP,
            repo_id="openai/clip-vit-base-patch32",
        ),
        "clip_vit_l14": ModelConfig(
            name="CLIP ViT-L/14",
            type=ModelType.CLIP,
            repo_id="openai/clip-vit-large-patch14",
        ),
        "siglip": ModelConfig(
            name="SigLIP",
            type=ModelType.CLIP,
            repo_id="google/siglip-so400m-patch14-384",
        ),
        "eva_clip": ModelConfig(
            name="EVA-CLIP",
            type=ModelType.CLIP,
            repo_id="BAAI/EVA-CLIP",
        ),
        "open_clip_g": ModelConfig(
            name="OpenCLIP-G",
            type=ModelType.CLIP,
            repo_id="laion/CLIP-ViT-g-14-laion2B-s12B-b42K",
        ),
    }

    @classmethod
    def get_all_models(cls) -> Dict[str, ModelConfig]:
        """Get all registered models"""
        return {
            **cls.DIFFUSION_MODELS,
            **cls.DEPTH_MODELS,
            **cls.SEGMENTATION_MODELS,
            **cls.FLOW_MODELS,
            **cls.CLIP_MODELS,
        }

    @classmethod
    def get_model_config(cls, model_id: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        return cls.get_all_models().get(model_id)

    @classmethod
    def list_models_by_type(cls, model_type: ModelType) -> Dict[str, ModelConfig]:
        """List all models of a specific type"""
        all_models = cls.get_all_models()
        return {k: v for k, v in all_models.items() if v.type == model_type}


class ModelLoader:
    """
    Unified model loader
    Handles downloading, caching, and loading models
    Similar to ComfyUI's model_management but adapted for PyTTI
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        device: Optional[Union[str, torch.device]] = None,
    ):
        """
        Initialize model loader

        Args:
            cache_dir: Directory for caching models (default: ~/.cache/pytti)
            device: Device to load models on (default: cuda if available)
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "pytti"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        elif isinstance(device, str):
            self.device = torch.device(device)
        else:
            self.device = device

        # Cache loaded models in memory
        self._loaded_models: Dict[str, Any] = {}

        logger.info(f"ModelLoader initialized")
        logger.info(f"  Cache directory: {self.cache_dir}")
        logger.info(f"  Device: {self.device}")

    def download_model(
        self,
        model_config: ModelConfig,
        force_download: bool = False,
    ) -> Path:
        """
        Download a model from Hugging Face Hub

        Args:
            model_config: Configuration for the model to download
            force_download: Force re-download even if cached

        Returns:
            Path to downloaded model directory or file
        """
        logger.info(f"Downloading model: {model_config.name}")

        # Create model-specific cache directory
        model_cache_dir = self.cache_dir / model_config.type.value / model_config.repo_id.replace("/", "_")

        if model_config.local_path and model_config.local_path.exists() and not force_download:
            logger.info(f"  Using local path: {model_config.local_path}")
            return model_config.local_path

        if model_cache_dir.exists() and not force_download:
            logger.info(f"  Found in cache: {model_cache_dir}")
            return model_cache_dir

        try:
            # Download entire model directory
            with vram_usage_mode(f"Downloading {model_config.name}"):
                snapshot_path = snapshot_download(
                    repo_id=model_config.repo_id,
                    cache_dir=str(self.cache_dir / "huggingface"),
                    local_dir=str(model_cache_dir),
                    local_dir_use_symlinks=False,
                )

            logger.info(f"  Downloaded to: {snapshot_path}")
            return Path(snapshot_path)

        except Exception as e:
            logger.error(f"Failed to download model {model_config.name}: {e}")
            raise

    def load_diffusion_model(
        self,
        model_id: str,
        variant: Optional[str] = "fp16",
        **kwargs,
    ) -> Any:
        """
        Load a diffusion model (Stable Diffusion, SDXL, Flux, etc.)

        Args:
            model_id: ID of the model to load
            variant: Model variant (fp16, fp32, etc.)
            **kwargs: Additional arguments for model loading

        Returns:
            Loaded diffusion model pipeline
        """
        from diffusers import (
            StableDiffusionPipeline,
            StableDiffusionXLPipeline,
            FluxPipeline,
            AutoPipelineForText2Image,
        )

        if model_id in self._loaded_models:
            logger.info(f"Using cached model: {model_id}")
            return self._loaded_models[model_id]

        model_config = ModelRegistry.get_model_config(model_id)
        if not model_config:
            raise ValueError(f"Unknown model ID: {model_id}")

        logger.info(f"Loading diffusion model: {model_config.name}")

        with vram_usage_mode(f"Loading {model_config.name}"):
            # Determine which pipeline to use
            if "flux" in model_id.lower():
                pipeline_cls = FluxPipeline
            elif "sdxl" in model_id.lower() or "sd3" in model_id.lower():
                pipeline_cls = StableDiffusionXLPipeline
            elif "sd" in model_id.lower():
                pipeline_cls = StableDiffusionPipeline
            else:
                # Auto-detect pipeline type
                pipeline_cls = AutoPipelineForText2Image

            # Load pipeline
            pipe = pipeline_cls.from_pretrained(
                model_config.repo_id,
                torch_dtype=torch.float16 if variant == "fp16" and self.device.type == "cuda" else torch.float32,
                variant=variant if self.device.type == "cuda" else None,
                **kwargs,
            )

            pipe = pipe.to(self.device)

            # Enable memory optimizations (ComfyUI-style)
            if self.device.type == "cuda":
                # Enable xformers if available
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                    logger.info("  Enabled xformers memory efficient attention")
                except:
                    pass

                # Enable model CPU offload for large models
                if "large" in model_id or "xl" in model_id:
                    try:
                        pipe.enable_model_cpu_offload()
                        logger.info("  Enabled model CPU offload")
                    except:
                        pass

        # Cache the loaded model
        self._loaded_models[model_id] = pipe

        logger.info(f"  Successfully loaded {model_config.name}")
        return pipe

    def load_depth_model(self, model_id: str, **kwargs) -> Any:
        """
        Load a depth estimation model

        Args:
            model_id: ID of the depth model to load
            **kwargs: Additional arguments for model loading

        Returns:
            Loaded depth estimation model
        """
        if model_id in self._loaded_models:
            logger.info(f"Using cached model: {model_id}")
            return self._loaded_models[model_id]

        model_config = ModelRegistry.get_model_config(model_id)
        if not model_config:
            raise ValueError(f"Unknown model ID: {model_id}")

        logger.info(f"Loading depth model: {model_config.name}")

        # Will implement specific depth model loaders
        # For now, placeholder
        raise NotImplementedError(f"Depth model loading for {model_id} not yet implemented")

    def load_segmentation_model(self, model_id: str, **kwargs) -> Any:
        """
        Load a segmentation model (SAM 2, etc.)

        Args:
            model_id: ID of the segmentation model to load
            **kwargs: Additional arguments for model loading

        Returns:
            Loaded segmentation model
        """
        if model_id in self._loaded_models:
            logger.info(f"Using cached model: {model_id}")
            return self._loaded_models[model_id]

        model_config = ModelRegistry.get_model_config(model_id)
        if not model_config:
            raise ValueError(f"Unknown model ID: {model_id}")

        logger.info(f"Loading segmentation model: {model_config.name}")

        # Will implement SAM 2 loader
        raise NotImplementedError(f"Segmentation model loading for {model_id} not yet implemented")

    def unload_model(self, model_id: str):
        """Unload a model from memory"""
        if model_id in self._loaded_models:
            del self._loaded_models[model_id]
            torch.cuda.empty_cache()
            logger.info(f"Unloaded model: {model_id}")

    def clear_cache(self):
        """Clear all loaded models from memory"""
        self._loaded_models.clear()
        torch.cuda.empty_cache()
        logger.info("Cleared model cache")

    def get_loaded_models(self) -> list[str]:
        """Get list of currently loaded model IDs"""
        return list(self._loaded_models.keys())


# Global model loader instance (ComfyUI-style singleton pattern)
_global_model_loader: Optional[ModelLoader] = None


def get_model_loader(
    cache_dir: Optional[Path] = None,
    device: Optional[Union[str, torch.device]] = None,
) -> ModelLoader:
    """
    Get the global model loader instance
    Creates it if it doesn't exist
    """
    global _global_model_loader

    if _global_model_loader is None:
        _global_model_loader = ModelLoader(cache_dir=cache_dir, device=device)

    return _global_model_loader


# Convenience functions
def load_model(model_id: str, **kwargs) -> Any:
    """Load any model by ID"""
    loader = get_model_loader()
    model_config = ModelRegistry.get_model_config(model_id)

    if not model_config:
        raise ValueError(f"Unknown model ID: {model_id}")

    if model_config.type == ModelType.DIFFUSION:
        return loader.load_diffusion_model(model_id, **kwargs)
    elif model_config.type == ModelType.DEPTH:
        return loader.load_depth_model(model_id, **kwargs)
    elif model_config.type == ModelType.SEGMENTATION:
        return loader.load_segmentation_model(model_id, **kwargs)
    else:
        raise NotImplementedError(f"Loading for model type {model_config.type} not yet implemented")


def list_available_models(model_type: Optional[ModelType] = None) -> Dict[str, ModelConfig]:
    """List all available models, optionally filtered by type"""
    if model_type:
        return ModelRegistry.list_models_by_type(model_type)
    return ModelRegistry.get_all_models()
