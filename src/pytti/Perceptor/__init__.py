"""
CLIP Perceptor Module

This module provides CLIP perceptor initialization and management.
Now uses ClipManager singleton for thread-safe, efficient resource management.
"""

import logging
import torch
from typing import List, Optional

from pytti.managers import ClipManager

logger = logging.getLogger(__name__)

# Backward compatibility: expose ClipManager functions at module level
# DEPRECATED: Use ClipManager.get_instance() directly in new code


def init_clip(clip_models: List[str], device: Optional[torch.device] = None) -> None:
    """
    Initialize CLIP perceptors.

    DEPRECATED: Use ClipManager.get_instance().initialize() for new code.
    This function is maintained for backward compatibility.

    Args:
        clip_models: List of CLIP model names (e.g., ["ViT-B/32"])
        device: Target device (defaults to CUDA if available)

    Example:
        >>> init_clip(["ViT-B/32", "ViT-L/14"])
        >>> # New code should use:
        >>> # ClipManager.get_instance().initialize(["ViT-B/32", "ViT-L/14"])
    """
    manager = ClipManager.get_instance()
    manager.initialize(clip_models, device)


def free_clip() -> None:
    """
    Free CLIP perceptors and clean up VRAM.

    DEPRECATED: Use ClipManager.get_instance().cleanup() for new code.
    This function is maintained for backward compatibility.

    Example:
        >>> free_clip()
        >>> # New code should use:
        >>> # ClipManager.get_instance().cleanup()
    """
    manager = ClipManager.get_instance()
    manager.cleanup()


def get_clip_perceptors() -> List:
    """
    Get currently loaded CLIP perceptors.

    DEPRECATED: Use ClipManager.get_instance().get_perceptors() for new code.
    This function is maintained for backward compatibility.

    Returns:
        List of CLIP perceptor models

    Raises:
        RuntimeError: If CLIP is not initialized

    Example:
        >>> init_clip(["ViT-B/32"])
        >>> perceptors = get_clip_perceptors()
        >>> # New code should use:
        >>> # perceptors = ClipManager.get_instance().get_perceptors()
    """
    manager = ClipManager.get_instance()
    return manager.get_perceptors()


# Legacy global variable for extreme backward compatibility
# DEPRECATED: Do not use in new code!
@property
def CLIP_PERCEPTORS():
    """
    Legacy global variable access.

    STRONGLY DEPRECATED: This exists only for extreme backward compatibility.
    Use ClipManager.get_instance().get_perceptors() instead.
    """
    try:
        manager = ClipManager.get_instance()
        if manager.is_initialized():
            return manager.get_perceptors()
    except Exception:
        pass
    return None
