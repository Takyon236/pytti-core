"""
Gallery Manager for PyTTI

Tracks and manages generated images with metadata.
"""

import json
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import threading

from loguru import logger


@dataclass
class ImageMetadata:
    """Metadata for a generated image."""

    image_path: Path
    prompt: str
    timestamp: float
    settings: Dict[str, Any]
    width: int
    height: int
    steps: int
    model: str
    favorite: bool = False
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        # Convert Path to string for JSON serialization
        if isinstance(self.image_path, Path):
            self.image_path = str(self.image_path)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["image_path"] = str(self.image_path)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageMetadata":
        """Create from dictionary."""
        data = data.copy()
        data["image_path"] = Path(data["image_path"])
        return cls(**data)

    def get_timestamp_str(self) -> str:
        """Get formatted timestamp string."""
        import datetime
        dt = datetime.datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def get_display_name(self) -> str:
        """Get display name for UI."""
        return Path(self.image_path).name


class GalleryManager:
    """
    Manages gallery of generated images.

    Features:
    - Track all generated images
    - Store metadata (prompt, settings, etc.)
    - Search and filter
    - Favorites
    - Tags for organization
    - Export metadata

    Usage:
        >>> manager = GalleryManager.get_instance()
        >>> manager.add_image(image_path, prompt, settings)
        >>> images = manager.get_recent(10)
        >>> favorites = manager.get_favorites()
    """

    _instance: Optional["GalleryManager"] = None
    _lock = threading.Lock()

    def __init__(
        self,
        gallery_dir: Optional[Path] = None,
        metadata_file: Optional[Path] = None
    ):
        """
        Initialize gallery manager.

        Args:
            gallery_dir: Directory containing images
            metadata_file: File to store metadata
        """
        if GalleryManager._instance is not None:
            raise RuntimeError(
                "GalleryManager is a singleton. Use get_instance() instead."
            )

        # Set directories
        if gallery_dir is None:
            gallery_dir = Path("outputs")
        if metadata_file is None:
            metadata_file = Path.home() / ".pytti" / "gallery_metadata.json"

        self.gallery_dir = gallery_dir
        self.metadata_file = metadata_file

        # Ensure metadata directory exists
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

        # Load metadata
        self._metadata: List[ImageMetadata] = []
        self._load_metadata()

        logger.info(f"GalleryManager initialized: {len(self._metadata)} images")

    @classmethod
    def get_instance(
        cls,
        gallery_dir: Optional[Path] = None,
        metadata_file: Optional[Path] = None
    ) -> "GalleryManager":
        """
        Get singleton instance.

        Args:
            gallery_dir: Gallery directory (only used on first call)
            metadata_file: Metadata file (only used on first call)

        Returns:
            GalleryManager instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = GalleryManager(gallery_dir, metadata_file)
        return cls._instance

    def add_image(
        self,
        image_path: Path,
        prompt: str,
        settings: Dict[str, Any],
        favorite: bool = False,
        tags: Optional[List[str]] = None
    ) -> ImageMetadata:
        """
        Add an image to the gallery.

        Args:
            image_path: Path to the image
            prompt: Generation prompt
            settings: Generation settings
            favorite: Mark as favorite
            tags: Optional tags

        Returns:
            Created ImageMetadata
        """
        # Extract key settings
        width = settings.get("width", 0)
        height = settings.get("height", 0)
        steps = settings.get("steps_per_scene", 0)
        model = settings.get("diffusion_model", "unknown")

        # Create metadata
        metadata = ImageMetadata(
            image_path=image_path,
            prompt=prompt,
            timestamp=time.time(),
            settings=settings,
            width=width,
            height=height,
            steps=steps,
            model=model,
            favorite=favorite,
            tags=tags or []
        )

        # Add to list
        self._metadata.append(metadata)

        # Save to disk
        self._save_metadata()

        logger.info(f"Added image to gallery: {image_path.name}")
        return metadata

    def get_all(self) -> List[ImageMetadata]:
        """Get all images (most recent first)."""
        return list(reversed(self._metadata))

    def get_recent(self, count: int = 20) -> List[ImageMetadata]:
        """
        Get most recent images.

        Args:
            count: Number of images to return

        Returns:
            List of ImageMetadata
        """
        return list(reversed(self._metadata[-count:]))

    def get_favorites(self) -> List[ImageMetadata]:
        """Get all favorite images."""
        favorites = [m for m in self._metadata if m.favorite]
        return list(reversed(favorites))

    def search_by_prompt(self, query: str, case_sensitive: bool = False) -> List[ImageMetadata]:
        """
        Search images by prompt.

        Args:
            query: Search query
            case_sensitive: Whether search is case-sensitive

        Returns:
            List of matching ImageMetadata
        """
        if not case_sensitive:
            query = query.lower()

        results = []
        for metadata in self._metadata:
            text = metadata.prompt if case_sensitive else metadata.prompt.lower()
            if query in text:
                results.append(metadata)

        return list(reversed(results))

    def search_by_tag(self, tag: str) -> List[ImageMetadata]:
        """
        Search images by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of matching ImageMetadata
        """
        results = [m for m in self._metadata if tag in m.tags]
        return list(reversed(results))

    def filter_by_model(self, model: str) -> List[ImageMetadata]:
        """
        Filter images by model.

        Args:
            model: Model name

        Returns:
            List of matching ImageMetadata
        """
        results = [m for m in self._metadata if m.model == model]
        return list(reversed(results))

    def filter_by_resolution(self, min_width: int = 0, min_height: int = 0) -> List[ImageMetadata]:
        """
        Filter images by resolution.

        Args:
            min_width: Minimum width
            min_height: Minimum height

        Returns:
            List of matching ImageMetadata
        """
        results = [
            m for m in self._metadata
            if m.width >= min_width and m.height >= min_height
        ]
        return list(reversed(results))

    def toggle_favorite(self, image_path: Path) -> bool:
        """
        Toggle favorite status of an image.

        Args:
            image_path: Path to image

        Returns:
            New favorite status
        """
        for metadata in self._metadata:
            if Path(metadata.image_path) == Path(image_path):
                metadata.favorite = not metadata.favorite
                self._save_metadata()
                return metadata.favorite

        logger.warning(f"Image not found for favorite toggle: {image_path}")
        return False

    def add_tag(self, image_path: Path, tag: str) -> bool:
        """
        Add a tag to an image.

        Args:
            image_path: Path to image
            tag: Tag to add

        Returns:
            True if successful
        """
        for metadata in self._metadata:
            if Path(metadata.image_path) == Path(image_path):
                if tag not in metadata.tags:
                    metadata.tags.append(tag)
                    self._save_metadata()
                return True

        return False

    def remove_tag(self, image_path: Path, tag: str) -> bool:
        """
        Remove a tag from an image.

        Args:
            image_path: Path to image
            tag: Tag to remove

        Returns:
            True if successful
        """
        for metadata in self._metadata:
            if Path(metadata.image_path) == Path(image_path):
                if tag in metadata.tags:
                    metadata.tags.remove(tag)
                    self._save_metadata()
                return True

        return False

    def delete_image(self, image_path: Path, delete_file: bool = False) -> bool:
        """
        Delete an image from gallery.

        Args:
            image_path: Path to image
            delete_file: Whether to delete the actual file

        Returns:
            True if deleted
        """
        original_len = len(self._metadata)
        self._metadata = [
            m for m in self._metadata
            if Path(m.image_path) != Path(image_path)
        ]

        if len(self._metadata) < original_len:
            # Delete file if requested
            if delete_file and image_path.exists():
                try:
                    image_path.unlink()
                    logger.info(f"Deleted image file: {image_path}")
                except Exception as e:
                    logger.error(f"Failed to delete image file: {e}")

            self._save_metadata()
            logger.info(f"Deleted image from gallery: {image_path}")
            return True

        return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get gallery statistics.

        Returns:
            Dictionary with statistics
        """
        if not self._metadata:
            return {
                "total_images": 0,
                "favorites": 0,
                "tagged": 0,
                "total_steps": 0,
                "avg_steps": 0,
            }

        total_steps = sum(m.steps for m in self._metadata)
        avg_steps = total_steps / len(self._metadata) if self._metadata else 0

        return {
            "total_images": len(self._metadata),
            "favorites": len([m for m in self._metadata if m.favorite]),
            "tagged": len([m for m in self._metadata if m.tags]),
            "total_steps": total_steps,
            "avg_steps": avg_steps,
            "unique_tags": len(set(tag for m in self._metadata for tag in m.tags)),
            "models_used": len(set(m.model for m in self._metadata)),
        }

    def scan_directory(self) -> int:
        """
        Scan gallery directory for images not in metadata.

        Returns:
            Number of new images found
        """
        if not self.gallery_dir.exists():
            return 0

        # Get existing image paths
        existing_paths = {Path(m.image_path) for m in self._metadata}

        # Scan for PNG files
        new_images = 0
        for image_path in self.gallery_dir.rglob("*.png"):
            if image_path not in existing_paths:
                # Add with minimal metadata
                self.add_image(
                    image_path=image_path,
                    prompt="(imported)",
                    settings={},
                    favorite=False
                )
                new_images += 1

        logger.info(f"Scanned directory: found {new_images} new images")
        return new_images

    def export_metadata(self, export_path: Path) -> None:
        """
        Export metadata to JSON file.

        Args:
            export_path: Path to export file
        """
        data = {
            "version": "1.0",
            "exported_at": time.time(),
            "images": [m.to_dict() for m in self._metadata]
        }

        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported metadata for {len(self._metadata)} images to {export_path}")

    def _load_metadata(self) -> None:
        """Load metadata from disk."""
        if not self.metadata_file.exists():
            logger.debug("No metadata file found, starting with empty gallery")
            return

        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)

            self._metadata = [
                ImageMetadata.from_dict(m) for m in data.get("images", [])
            ]

            logger.info(f"Loaded metadata for {len(self._metadata)} images")

        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            self._metadata = []

    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            data = {
                "version": "1.0",
                "images": [m.to_dict() for m in self._metadata]
            }

            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved metadata for {len(self._metadata)} images")

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None
