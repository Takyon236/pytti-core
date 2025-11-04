"""
Configuration Manager for PyTTI

Handles loading, saving, and managing user configuration.
Provides settings persistence so users don't have to re-enter preferences.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import threading

from loguru import logger


@dataclass
class DefaultConfig:
    """Default configuration values."""

    # Image generation
    width: int = 1024
    height: int = 1024
    steps_per_scene: int = 100
    learning_rate: float = 0.5
    seed: int = -1  # -1 = random

    # Models
    diffusion_model: str = "Stable Diffusion XL"
    clip_model: str = "ViT-B/32 (Fast)"

    # CLIP parameters
    cutouts: int = 40
    cut_pow: float = 1.5

    # Advanced
    ema_val: float = 0.99
    save_every: int = 10

    # Output
    file_namespace: str = "pytti_output"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ConfigManager:
    """
    Manages user configuration with persistence.

    Features:
    - Load/save user preferences
    - Default configuration
    - Validation integration
    - Thread-safe access
    - Automatic backup

    Usage:
        >>> manager = ConfigManager.get_instance()
        >>> config = manager.load_config()
        >>> config["width"] = 512
        >>> manager.save_config(config)
    """

    _instance: Optional["ConfigManager"] = None
    _lock = threading.Lock()

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory to store config files (defaults to ~/.pytti)
        """
        if ConfigManager._instance is not None:
            raise RuntimeError(
                "ConfigManager is a singleton. Use ConfigManager.get_instance() instead."
            )

        # Set config directory
        if config_dir is None:
            config_dir = Path.home() / ".pytti"

        self.config_dir = config_dir
        self.config_file = config_dir / "config.json"
        self.backup_file = config_dir / "config.backup.json"

        # Ensure directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load or create default config
        self._config = self._load_or_default()

        logger.info(f"ConfigManager initialized: {self.config_file}")

    @classmethod
    def get_instance(cls, config_dir: Optional[Path] = None) -> "ConfigManager":
        """
        Get singleton instance of ConfigManager.

        Args:
            config_dir: Config directory (only used on first call)

        Returns:
            ConfigManager singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ConfigManager(config_dir)
        return cls._instance

    def load_config(self) -> Dict[str, Any]:
        """
        Load current configuration.

        Returns:
            Configuration dictionary
        """
        return self._config.copy()

    def save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration dictionary to save

        Raises:
            IOError: If save fails
        """
        try:
            # Backup existing config
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r') as f:
                        backup_data = f.read()
                    with open(self.backup_file, 'w') as f:
                        f.write(backup_data)
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")

            # Save new config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

            # Update in-memory config
            self._config = config.copy()

            logger.info(f"Configuration saved: {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise IOError(f"Could not save configuration: {e}") from e

    def update_config(self, **kwargs: Any) -> None:
        """
        Update specific configuration values.

        Args:
            **kwargs: Configuration keys and values to update

        Example:
            >>> manager = ConfigManager.get_instance()
            >>> manager.update_config(width=512, height=512)
        """
        self._config.update(kwargs)
        self.save_config(self._config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value
        self.save_config(self._config)

    def reset_to_defaults(self) -> Dict[str, Any]:
        """
        Reset configuration to defaults.

        Returns:
            Default configuration dictionary
        """
        logger.info("Resetting configuration to defaults")
        defaults = DefaultConfig().to_dict()
        self.save_config(defaults)
        return defaults.copy()

    def _load_or_default(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default.

        Returns:
            Configuration dictionary
        """
        # Try to load existing config
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")

                # Merge with defaults (add any new keys)
                defaults = DefaultConfig().to_dict()
                for key, value in defaults.items():
                    if key not in config:
                        config[key] = value
                        logger.info(f"Added new config key: {key} = {value}")

                return config

            except Exception as e:
                logger.warning(f"Failed to load config, trying backup: {e}")

                # Try backup
                if self.backup_file.exists():
                    try:
                        with open(self.backup_file, 'r') as f:
                            config = json.load(f)
                        logger.info("Loaded configuration from backup")
                        return config
                    except Exception as backup_error:
                        logger.error(f"Backup also failed: {backup_error}")

        # Create default config
        logger.info("Creating default configuration")
        defaults = DefaultConfig().to_dict()

        # Save defaults
        try:
            with open(self.config_file, 'w') as f:
                json.dump(defaults, f, indent=2)
            logger.info(f"Saved default configuration to {self.config_file}")
        except Exception as e:
            logger.warning(f"Failed to save default config: {e}")

        return defaults

    def get_config_file_path(self) -> Path:
        """Get path to configuration file."""
        return self.config_file

    def has_config_file(self) -> bool:
        """Check if configuration file exists."""
        return self.config_file.exists()

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset singleton instance (mainly for testing).

        WARNING: Only use in tests or during shutdown.
        """
        with cls._lock:
            cls._instance = None


# Convenience functions for common operations

def load_user_config() -> Dict[str, Any]:
    """
    Load user configuration.

    Returns:
        Configuration dictionary
    """
    return ConfigManager.get_instance().load_config()


def save_user_config(config: Dict[str, Any]) -> None:
    """
    Save user configuration.

    Args:
        config: Configuration to save
    """
    ConfigManager.get_instance().save_config(config)


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration.

    Returns:
        Default configuration dictionary
    """
    return DefaultConfig().to_dict()
