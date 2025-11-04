"""
Resource managers for PyTTI.

This module provides singleton managers for efficient resource management:
- ClipManager: Thread-safe CLIP model management
- ModelManager: Model caching and lifecycle management
"""

from pytti.managers.clip_manager import ClipManager
from pytti.managers.model_manager import ModelManager

__all__ = ["ClipManager", "ModelManager"]
