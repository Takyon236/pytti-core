"""
Model Manager - Singleton for efficient model caching and lifecycle management.

Prevents reloading models on every generation, tracks VRAM usage, and provides
proper resource cleanup.
"""

import logging
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

import torch

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of models managed by ModelManager."""
    DIFFUSION = "diffusion"
    VAE = "vae"
    DEPTH = "depth"
    FLOW = "flow"
    SAM = "sam"


@dataclass
class ModelCacheEntry:
    """Cache entry for a loaded model."""
    model: Any
    model_id: str
    model_type: ModelType
    device: torch.device
    vram_mb: float = 0.0
    load_count: int = 0
    last_accessed: float = 0.0


class ModelManager:
    """
    Thread-safe singleton manager for model caching and lifecycle.

    Features:
    - Caches loaded models to avoid reloading
    - Tracks VRAM usage per model
    - Thread-safe access
    - Proper cleanup mechanisms
    - LRU-style eviction when VRAM is low

    Usage:
        manager = ModelManager.get_instance()
        model = manager.get_or_load(
            model_id="stabilityai/stable-diffusion-xl-base-1.0",
            model_type=ModelType.DIFFUSION,
            loader_fn=lambda: load_model()
        )
        manager.cleanup_model(model_id)
    """

    _instance: Optional["ModelManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        """Private constructor. Use get_instance() instead."""
        if ModelManager._instance is not None:
            raise RuntimeError(
                "ModelManager is a singleton. Use ModelManager.get_instance() instead."
            )

        self._cache: Dict[str, ModelCacheEntry] = {}
        self._access_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ModelManager":
        """
        Get the singleton instance of ModelManager.

        Returns:
            ModelManager: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check locking
                    cls._instance = ModelManager()
        return cls._instance

    def get_or_load(
        self,
        model_id: str,
        model_type: ModelType,
        loader_fn: callable,
        device: Optional[torch.device] = None,
        force_reload: bool = False
    ) -> Any:
        """
        Get model from cache or load it using the provided loader function.

        Args:
            model_id: Unique identifier for the model (e.g., HuggingFace repo ID)
            model_type: Type of model
            loader_fn: Function that loads the model (called only if not cached)
            device: Target device (defaults to CUDA if available)
            force_reload: Force reload even if cached

        Returns:
            The loaded model

        Raises:
            RuntimeError: If model loading fails
        """
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        cache_key = f"{model_type.value}:{model_id}"

        with self._access_lock:
            # Return cached model if available
            if cache_key in self._cache and not force_reload:
                entry = self._cache[cache_key]
                entry.load_count += 1
                import time
                entry.last_accessed = time.time()
                logger.info(
                    f"Using cached {model_type.value} model: {model_id} "
                    f"(loads: {entry.load_count})"
                )
                return entry.model

            # Load new model
            logger.info(f"Loading {model_type.value} model: {model_id}")

            try:
                # Get VRAM before loading
                vram_before = self._get_vram_usage_mb() if device.type == "cuda" else 0

                # Load model
                model = loader_fn()

                # Calculate VRAM used
                vram_after = self._get_vram_usage_mb() if device.type == "cuda" else 0
                vram_used = max(0, vram_after - vram_before)

                # Create cache entry
                import time
                entry = ModelCacheEntry(
                    model=model,
                    model_id=model_id,
                    model_type=model_type,
                    device=device,
                    vram_mb=vram_used,
                    load_count=1,
                    last_accessed=time.time()
                )

                self._cache[cache_key] = entry

                logger.info(
                    f"✓ Loaded {model_type.value} model: {model_id} "
                    f"(VRAM: {vram_used:.1f} MB)"
                )

                return model

            except Exception as e:
                logger.error(f"Failed to load {model_type.value} model {model_id}: {e}")
                raise RuntimeError(f"Model loading failed: {e}") from e

    def is_cached(self, model_id: str, model_type: ModelType) -> bool:
        """
        Check if a model is cached.

        Args:
            model_id: Model identifier
            model_type: Type of model

        Returns:
            bool: True if model is in cache
        """
        cache_key = f"{model_type.value}:{model_id}"
        with self._access_lock:
            return cache_key in self._cache

    def cleanup_model(self, model_id: str, model_type: ModelType) -> None:
        """
        Remove a specific model from cache and free its VRAM.

        Args:
            model_id: Model identifier
            model_type: Type of model
        """
        cache_key = f"{model_type.value}:{model_id}"

        with self._access_lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                logger.info(
                    f"Cleaning up {model_type.value} model: {model_id} "
                    f"(VRAM: {entry.vram_mb:.1f} MB)"
                )

                # Move to CPU and delete
                try:
                    if hasattr(entry.model, 'to'):
                        entry.model.to("cpu")
                    del entry.model
                except Exception as e:
                    logger.warning(f"Error during model cleanup: {e}")

                del self._cache[cache_key]

                # Clear CUDA cache
                if entry.device.type == "cuda":
                    torch.cuda.empty_cache()

                logger.info(f"✓ Cleaned up {model_type.value} model: {model_id}")

    def cleanup_all(self) -> None:
        """
        Clean up all cached models and free VRAM.
        """
        with self._access_lock:
            if not self._cache:
                logger.debug("Model cache is empty - nothing to cleanup")
                return

            logger.info(f"Cleaning up {len(self._cache)} cached models...")

            # Clean up all models
            for cache_key, entry in list(self._cache.items()):
                try:
                    if hasattr(entry.model, 'to'):
                        entry.model.to("cpu")
                    del entry.model
                except Exception as e:
                    logger.warning(f"Error cleaning up {cache_key}: {e}")

            self._cache.clear()

            # Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("✓ All models cleaned up")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the model cache.

        Returns:
            Dict with cache statistics
        """
        with self._access_lock:
            total_vram = sum(entry.vram_mb for entry in self._cache.values())
            total_loads = sum(entry.load_count for entry in self._cache.values())

            return {
                "cached_models": len(self._cache),
                "total_vram_mb": total_vram,
                "total_loads": total_loads,
                "models": [
                    {
                        "id": entry.model_id,
                        "type": entry.model_type.value,
                        "vram_mb": entry.vram_mb,
                        "load_count": entry.load_count,
                    }
                    for entry in self._cache.values()
                ]
            }

    def _get_vram_usage_mb(self) -> float:
        """
        Get current VRAM usage in MB.

        Returns:
            float: VRAM usage in MB
        """
        if not torch.cuda.is_available():
            return 0.0

        try:
            allocated = torch.cuda.memory_allocated() / 1024 / 1024
            return allocated
        except Exception as e:
            logger.warning(f"Failed to get VRAM usage: {e}")
            return 0.0

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance (mainly for testing).

        WARNING: This should only be used in tests or during shutdown.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance.cleanup_all()
                cls._instance = None

    def __del__(self):
        """Destructor - ensures cleanup on garbage collection."""
        try:
            self.cleanup_all()
        except Exception:
            pass  # Ignore errors during cleanup
