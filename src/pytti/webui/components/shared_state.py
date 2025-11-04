"""
Shared state management for PyTTI Web UI

Manages models, generation state, and session data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import threading

import torch
from loguru import logger

from pytti.model_loader import get_model_loader, ModelLoader


@dataclass
class GenerationState:
    """State of current generation"""
    is_generating: bool = False
    current_step: int = 0
    total_steps: int = 0
    current_image: Optional[Any] = None
    error_message: Optional[str] = None
    should_stop: bool = False


@dataclass
class GenerationHistory:
    """History of generated images"""
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    output_dir: Path = field(default_factory=lambda: Path("outputs"))

    def add_output(
        self,
        image_path: Path,
        prompt: str,
        settings: Dict[str, Any]
    ):
        """Add generated output to history"""
        self.outputs.append({
            "image_path": image_path,
            "prompt": prompt,
            "settings": settings,
        })

    def get_latest(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get latest N outputs"""
        return self.outputs[-n:]


class SharedState:
    """
    Shared state across all UI components

    Manages:
    - Model loading and caching
    - Generation state
    - Output history
    - Session settings
    """

    def __init__(self, device: Optional[torch.device] = None):
        """Initialize shared state"""
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.device = device
        self.model_loader: Optional[ModelLoader] = None
        self.generation_state = GenerationState()
        self.history = GenerationHistory()

        # Thread lock for state updates
        self.lock = threading.Lock()

        # Session settings (persisted across generations)
        self.session_settings: Dict[str, Any] = {}

        logger.info(f"SharedState initialized on {device}")

    def get_model_loader(self) -> ModelLoader:
        """Get or create model loader (lazy initialization)"""
        if self.model_loader is None:
            logger.info("Initializing ModelLoader...")
            self.model_loader = get_model_loader(device=self.device)
        return self.model_loader

    def update_generation_state(
        self,
        is_generating: Optional[bool] = None,
        current_step: Optional[int] = None,
        total_steps: Optional[int] = None,
        current_image: Optional[Any] = None,
        error_message: Optional[str] = None,
    ):
        """Thread-safe update of generation state"""
        with self.lock:
            if is_generating is not None:
                self.generation_state.is_generating = is_generating
            if current_step is not None:
                self.generation_state.current_step = current_step
            if total_steps is not None:
                self.generation_state.total_steps = total_steps
            if current_image is not None:
                self.generation_state.current_image = current_image
            if error_message is not None:
                self.generation_state.error_message = error_message

    def request_stop(self):
        """Request stopping current generation"""
        with self.lock:
            self.generation_state.should_stop = True
            logger.info("Stop requested")

    def reset_stop_flag(self):
        """Reset stop flag for new generation"""
        with self.lock:
            self.generation_state.should_stop = False

    def check_should_stop(self) -> bool:
        """Check if generation should stop"""
        with self.lock:
            return self.generation_state.should_stop

    def get_generation_progress(self) -> tuple[int, int, bool]:
        """
        Get current generation progress

        Returns:
            Tuple of (current_step, total_steps, is_generating)
        """
        with self.lock:
            return (
                self.generation_state.current_step,
                self.generation_state.total_steps,
                self.generation_state.is_generating,
            )

    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up SharedState...")
        if self.model_loader is not None:
            # Unload models to free VRAM
            # ModelLoader handles cleanup internally
            pass

        # Clear CUDA cache if using GPU
        if self.device.type == "cuda":
            torch.cuda.empty_cache()
