"""
CLIP Model Manager - Thread-safe singleton for CLIP perceptor management.

This replaces the global CLIP_PERCEPTORS variable with a proper singleton pattern.
"""

import logging
import threading
from typing import List, Optional

import torch
from clip import clip

from pytti import vram_usage_mode

logger = logging.getLogger(__name__)


class ClipManager:
    """
    Thread-safe singleton manager for CLIP perceptors.

    Features:
    - Thread-safe initialization and access
    - Proper resource cleanup
    - Configurable model selection
    - Lazy loading
    - VRAM tracking

    Usage:
        manager = ClipManager.get_instance()
        manager.initialize(["ViT-B/32", "ViT-L/14"], device)
        perceptors = manager.get_perceptors()
        manager.cleanup()
    """

    _instance: Optional["ClipManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        """Private constructor. Use get_instance() instead."""
        if ClipManager._instance is not None:
            raise RuntimeError(
                "ClipManager is a singleton. Use ClipManager.get_instance() instead."
            )

        self._perceptors: Optional[List] = None
        self._device: Optional[torch.device] = None
        self._model_names: List[str] = []
        self._initialized = False
        self._init_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ClipManager":
        """
        Get the singleton instance of ClipManager.

        Returns:
            ClipManager: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check locking
                    cls._instance = ClipManager()
        return cls._instance

    @vram_usage_mode("CLIP")
    def initialize(
        self,
        model_names: List[str],
        device: Optional[torch.device] = None,
        force_reload: bool = False
    ) -> None:
        """
        Initialize CLIP perceptors with specified models.

        Args:
            model_names: List of CLIP model names (e.g., ["ViT-B/32", "ViT-L/14"])
            device: Target device (defaults to CUDA if available)
            force_reload: Force reload even if already initialized

        Raises:
            RuntimeError: If model loading fails
        """
        with self._init_lock:
            # Skip if already initialized with same models
            if (
                self._initialized
                and self._model_names == model_names
                and not force_reload
            ):
                logger.info(
                    f"CLIP already initialized with models: {model_names}"
                )
                return

            # Cleanup existing models if reloading
            if self._initialized and force_reload:
                logger.info("Force reload requested - cleaning up existing CLIP models")
                self._cleanup_internal()

            # Set device
            if device is None:
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            logger.info(f"Initializing CLIP with models: {model_names} on {device}")

            try:
                # Load CLIP models
                self._perceptors = []
                for model_name in model_names:
                    logger.info(f"  Loading {model_name}...")
                    model, _ = clip.load(model_name, jit=False)
                    model = (
                        model.eval()
                        .requires_grad_(False)
                        .to(device, memory_format=torch.channels_last)
                    )
                    self._perceptors.append(model)
                    logger.info(f"  ✓ {model_name} loaded")

                self._device = device
                self._model_names = model_names.copy()
                self._initialized = True

                logger.info(
                    f"✓ CLIP initialized successfully with {len(self._perceptors)} models"
                )

            except Exception as e:
                logger.error(f"Failed to initialize CLIP: {e}")
                self._cleanup_internal()
                raise RuntimeError(f"CLIP initialization failed: {e}") from e

    def get_perceptors(self) -> List:
        """
        Get the loaded CLIP perceptors.

        Returns:
            List of CLIP perceptor models

        Raises:
            RuntimeError: If CLIP is not initialized
        """
        if not self._initialized or self._perceptors is None:
            raise RuntimeError(
                "CLIP not initialized. Call initialize() first."
            )
        return self._perceptors

    def is_initialized(self) -> bool:
        """
        Check if CLIP is initialized.

        Returns:
            bool: True if initialized
        """
        return self._initialized and self._perceptors is not None

    def get_model_names(self) -> List[str]:
        """
        Get the names of currently loaded models.

        Returns:
            List of model names
        """
        return self._model_names.copy()

    def get_device(self) -> Optional[torch.device]:
        """
        Get the device CLIP models are loaded on.

        Returns:
            torch.device or None if not initialized
        """
        return self._device

    def _cleanup_internal(self) -> None:
        """Internal cleanup method (not thread-safe)."""
        if self._perceptors is not None:
            # Move models to CPU and delete
            for perceptor in self._perceptors:
                try:
                    perceptor.to("cpu")
                    del perceptor
                except Exception as e:
                    logger.warning(f"Error during perceptor cleanup: {e}")

            self._perceptors = None

        # Clear CUDA cache if we were using GPU
        if self._device is not None and self._device.type == "cuda":
            try:
                torch.cuda.empty_cache()
            except Exception as e:
                logger.warning(f"Error clearing CUDA cache: {e}")

        self._device = None
        self._model_names = []
        self._initialized = False

    def cleanup(self) -> None:
        """
        Clean up CLIP perceptors and free VRAM.

        Thread-safe cleanup that moves models to CPU and clears CUDA cache.
        """
        with self._init_lock:
            if self._initialized:
                logger.info("Cleaning up CLIP perceptors...")
                self._cleanup_internal()
                logger.info("✓ CLIP cleanup complete")
            else:
                logger.debug("CLIP not initialized - nothing to cleanup")

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance (mainly for testing).

        WARNING: This should only be used in tests or during shutdown.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance.cleanup()
                cls._instance = None

    def __del__(self):
        """Destructor - ensures cleanup on garbage collection."""
        try:
            self._cleanup_internal()
        except Exception:
            pass  # Ignore errors during cleanup


# Backward compatibility functions for legacy code
_legacy_warned = False


def init_clip(clip_models: List[str], device: Optional[torch.device] = None) -> None:
    """
    Legacy function for backward compatibility.

    DEPRECATED: Use ClipManager.get_instance().initialize() instead.

    Args:
        clip_models: List of CLIP model names
        device: Target device
    """
    global _legacy_warned
    if not _legacy_warned:
        logger.warning(
            "init_clip() is deprecated. Use ClipManager.get_instance().initialize() instead."
        )
        _legacy_warned = True

    manager = ClipManager.get_instance()
    manager.initialize(clip_models, device)


def free_clip() -> None:
    """
    Legacy function for backward compatibility.

    DEPRECATED: Use ClipManager.get_instance().cleanup() instead.
    """
    global _legacy_warned
    if not _legacy_warned:
        logger.warning(
            "free_clip() is deprecated. Use ClipManager.get_instance().cleanup() instead."
        )
        _legacy_warned = True

    manager = ClipManager.get_instance()
    manager.cleanup()


def get_clip_perceptors() -> List:
    """
    Legacy function to get CLIP perceptors.

    DEPRECATED: Use ClipManager.get_instance().get_perceptors() instead.

    Returns:
        List of CLIP perceptor models
    """
    global _legacy_warned
    if not _legacy_warned:
        logger.warning(
            "get_clip_perceptors() is deprecated. Use ClipManager.get_instance().get_perceptors() instead."
        )
        _legacy_warned = True

    manager = ClipManager.get_instance()
    return manager.get_perceptors()
