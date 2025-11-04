"""
Preset Manager for PyTTI

Manages generation settings presets (Fast/Balanced/Quality + custom).
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import threading

from loguru import logger


# Built-in presets
BUILTIN_PRESETS = {
    "Fast (Draft Quality)": {
        "width": 512,
        "height": 512,
        "steps_per_scene": 50,
        "learning_rate": 0.8,
        "cutouts": 20,
        "cut_pow": 1.0,
        "ema_val": 0.95,
        "save_every": 25,
        "clip_model": "ViT-B/32 (Fast)",
        "diffusion_model": "Stable Diffusion XL",
    },
    "Balanced (Recommended)": {
        "width": 1024,
        "height": 1024,
        "steps_per_scene": 100,
        "learning_rate": 0.5,
        "cutouts": 40,
        "cut_pow": 1.5,
        "ema_val": 0.99,
        "save_every": 10,
        "clip_model": "ViT-B/16 (Balanced)",
        "diffusion_model": "Stable Diffusion XL",
    },
    "Quality (Slow)": {
        "width": 1024,
        "height": 1024,
        "steps_per_scene": 200,
        "learning_rate": 0.3,
        "cutouts": 64,
        "cut_pow": 2.0,
        "ema_val": 0.995,
        "save_every": 10,
        "clip_model": "ViT-L/14 (Quality)",
        "diffusion_model": "Stable Diffusion XL",
    },
    "High Resolution": {
        "width": 1536,
        "height": 1536,
        "steps_per_scene": 150,
        "learning_rate": 0.4,
        "cutouts": 48,
        "cut_pow": 1.5,
        "ema_val": 0.99,
        "save_every": 15,
        "clip_model": "ViT-B/16 (Balanced)",
        "diffusion_model": "Stable Diffusion XL",
    },
    "Animation (Smooth)": {
        "width": 768,
        "height": 768,
        "steps_per_scene": 120,
        "learning_rate": 0.4,
        "cutouts": 32,
        "cut_pow": 1.2,
        "ema_val": 0.995,  # Higher EMA for smoother transitions
        "save_every": 5,
        "clip_model": "ViT-B/32 (Fast)",
        "diffusion_model": "Stable Diffusion XL",
    },
}


class PresetManager:
    """
    Manages generation settings presets.

    Features:
    - Built-in presets (Fast/Balanced/Quality)
    - Custom preset save/load
    - Export/import presets
    - Preset validation

    Usage:
        >>> manager = PresetManager.get_instance()
        >>> settings = manager.get_preset("Balanced (Recommended)")
        >>> manager.save_custom_preset("My Settings", custom_settings)
        >>> presets = manager.list_presets()
    """

    _instance: Optional["PresetManager"] = None
    _lock = threading.Lock()

    def __init__(self, presets_dir: Optional[Path] = None):
        """
        Initialize preset manager.

        Args:
            presets_dir: Directory to store custom presets
        """
        if PresetManager._instance is not None:
            raise RuntimeError(
                "PresetManager is a singleton. Use get_instance() instead."
            )

        # Set presets directory
        if presets_dir is None:
            presets_dir = Path.home() / ".pytti" / "presets"

        self.presets_dir = presets_dir
        self.presets_dir.mkdir(parents=True, exist_ok=True)

        # Load custom presets
        self._custom_presets: Dict[str, Dict[str, Any]] = {}
        self._load_custom_presets()

        logger.info(f"PresetManager initialized: {len(self._custom_presets)} custom presets")

    @classmethod
    def get_instance(cls, presets_dir: Optional[Path] = None) -> "PresetManager":
        """
        Get singleton instance.

        Args:
            presets_dir: Presets directory (only used on first call)

        Returns:
            PresetManager instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = PresetManager(presets_dir)
        return cls._instance

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a preset by name.

        Args:
            name: Preset name

        Returns:
            Preset settings dict or None if not found
        """
        # Check built-in presets first
        if name in BUILTIN_PRESETS:
            return BUILTIN_PRESETS[name].copy()

        # Check custom presets
        if name in self._custom_presets:
            return self._custom_presets[name].copy()

        logger.warning(f"Preset not found: {name}")
        return None

    def list_presets(self, include_custom: bool = True) -> List[str]:
        """
        List all available presets.

        Args:
            include_custom: Whether to include custom presets

        Returns:
            List of preset names
        """
        presets = list(BUILTIN_PRESETS.keys())

        if include_custom:
            presets.extend(self._custom_presets.keys())

        return presets

    def list_builtin_presets(self) -> List[str]:
        """Get list of built-in preset names."""
        return list(BUILTIN_PRESETS.keys())

    def list_custom_presets(self) -> List[str]:
        """Get list of custom preset names."""
        return list(self._custom_presets.keys())

    def save_custom_preset(self, name: str, settings: Dict[str, Any]) -> bool:
        """
        Save a custom preset.

        Args:
            name: Preset name
            settings: Settings dictionary

        Returns:
            True if successful
        """
        # Don't allow overwriting built-in presets
        if name in BUILTIN_PRESETS:
            logger.error(f"Cannot overwrite built-in preset: {name}")
            return False

        # Save to memory
        self._custom_presets[name] = settings.copy()

        # Save to disk
        preset_file = self.presets_dir / f"{self._sanitize_filename(name)}.json"
        try:
            with open(preset_file, 'w') as f:
                json.dump({
                    "name": name,
                    "settings": settings
                }, f, indent=2)

            logger.info(f"Saved custom preset: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save preset: {e}")
            return False

    def delete_custom_preset(self, name: str) -> bool:
        """
        Delete a custom preset.

        Args:
            name: Preset name

        Returns:
            True if successful
        """
        # Can't delete built-in presets
        if name in BUILTIN_PRESETS:
            logger.error(f"Cannot delete built-in preset: {name}")
            return False

        if name not in self._custom_presets:
            logger.warning(f"Custom preset not found: {name}")
            return False

        # Remove from memory
        del self._custom_presets[name]

        # Remove from disk
        preset_file = self.presets_dir / f"{self._sanitize_filename(name)}.json"
        try:
            if preset_file.exists():
                preset_file.unlink()

            logger.info(f"Deleted custom preset: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete preset: {e}")
            return False

    def export_preset(self, name: str, export_path: Path) -> bool:
        """
        Export a preset to a JSON file.

        Args:
            name: Preset name
            export_path: Export file path

        Returns:
            True if successful
        """
        preset = self.get_preset(name)
        if not preset:
            logger.error(f"Preset not found: {name}")
            return False

        try:
            with open(export_path, 'w') as f:
                json.dump({
                    "name": name,
                    "settings": preset,
                    "exported_from": "PyTTI"
                }, f, indent=2)

            logger.info(f"Exported preset '{name}' to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export preset: {e}")
            return False

    def import_preset(self, import_path: Path, name_override: Optional[str] = None) -> bool:
        """
        Import a preset from a JSON file.

        Args:
            import_path: Import file path
            name_override: Optional name override

        Returns:
            True if successful
        """
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)

            name = name_override or data.get("name", "Imported Preset")
            settings = data.get("settings", {})

            return self.save_custom_preset(name, settings)

        except Exception as e:
            logger.error(f"Failed to import preset: {e}")
            return False

    def _load_custom_presets(self) -> None:
        """Load all custom presets from disk."""
        if not self.presets_dir.exists():
            return

        for preset_file in self.presets_dir.glob("*.json"):
            try:
                with open(preset_file, 'r') as f:
                    data = json.load(f)

                name = data.get("name")
                settings = data.get("settings")

                if name and settings:
                    self._custom_presets[name] = settings
                    logger.debug(f"Loaded custom preset: {name}")

            except Exception as e:
                logger.warning(f"Failed to load preset from {preset_file}: {e}")

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize preset name for use as filename."""
        # Remove/replace characters that are invalid in filenames
        invalid_chars = '<>:"/\\|?*'
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        return sanitized

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None


# Convenience functions

def get_preset(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a preset by name.

    Args:
        name: Preset name

    Returns:
        Preset settings dict or None
    """
    return PresetManager.get_instance().get_preset(name)


def list_all_presets() -> List[str]:
    """Get list of all available presets."""
    return PresetManager.get_instance().list_presets()


def save_preset(name: str, settings: Dict[str, Any]) -> bool:
    """
    Save a custom preset.

    Args:
        name: Preset name
        settings: Settings dictionary

    Returns:
        True if successful
    """
    return PresetManager.get_instance().save_custom_preset(name, settings)
