"""
Prompt History Manager for PyTTI

Tracks and manages prompt history with persistence.
Users can quickly re-use previous prompts and search history.
"""

import json
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import threading

from loguru import logger


@dataclass
class PromptEntry:
    """A single prompt history entry."""

    prompt: str
    timestamp: float
    settings: Optional[Dict[str, Any]] = None
    favorite: bool = False
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptEntry":
        """Create from dictionary."""
        return cls(**data)

    def get_display_text(self, max_length: int = 50) -> str:
        """
        Get display text for UI.

        Args:
            max_length: Maximum length before truncation

        Returns:
            Formatted display string
        """
        text = self.prompt
        if len(text) > max_length:
            text = text[:max_length-3] + "..."

        # Add favorite star
        if self.favorite:
            text = "⭐ " + text

        return text

    def get_timestamp_str(self) -> str:
        """Get formatted timestamp string."""
        import datetime
        dt = datetime.datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class PromptHistoryManager:
    """
    Manages prompt history with persistence.

    Features:
    - Save all prompts with timestamps
    - Search and filter history
    - Favorite prompts
    - Tag prompts for organization
    - Export/import history
    - Limit history size (configurable)

    Usage:
        >>> manager = PromptHistoryManager.get_instance()
        >>> manager.add_prompt("a beautiful sunset")
        >>> recent = manager.get_recent(10)
        >>> results = manager.search("sunset")
    """

    _instance: Optional["PromptHistoryManager"] = None
    _lock = threading.Lock()

    def __init__(self, history_dir: Optional[Path] = None, max_entries: int = 1000):
        """
        Initialize prompt history manager.

        Args:
            history_dir: Directory to store history (defaults to ~/.pytti)
            max_entries: Maximum number of history entries to keep
        """
        if PromptHistoryManager._instance is not None:
            raise RuntimeError(
                "PromptHistoryManager is a singleton. Use get_instance() instead."
            )

        # Set history directory
        if history_dir is None:
            history_dir = Path.home() / ".pytti"

        self.history_dir = history_dir
        self.history_file = history_dir / "prompt_history.json"
        self.max_entries = max_entries

        # Ensure directory exists
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Load history
        self._entries: List[PromptEntry] = []
        self._load_history()

        logger.info(f"PromptHistoryManager initialized: {len(self._entries)} entries")

    @classmethod
    def get_instance(
        cls,
        history_dir: Optional[Path] = None,
        max_entries: int = 1000
    ) -> "PromptHistoryManager":
        """
        Get singleton instance.

        Args:
            history_dir: History directory (only used on first call)
            max_entries: Max entries (only used on first call)

        Returns:
            PromptHistoryManager instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = PromptHistoryManager(history_dir, max_entries)
        return cls._instance

    def add_prompt(
        self,
        prompt: str,
        settings: Optional[Dict[str, Any]] = None,
        favorite: bool = False,
        tags: Optional[List[str]] = None
    ) -> PromptEntry:
        """
        Add a prompt to history.

        Args:
            prompt: The prompt text
            settings: Optional generation settings
            favorite: Mark as favorite
            tags: Optional tags for organization

        Returns:
            Created PromptEntry
        """
        # Check for duplicates (don't add same prompt twice in a row)
        if self._entries and self._entries[-1].prompt == prompt:
            logger.debug(f"Skipping duplicate prompt: {prompt[:50]}...")
            return self._entries[-1]

        # Create entry
        entry = PromptEntry(
            prompt=prompt,
            timestamp=time.time(),
            settings=settings,
            favorite=favorite,
            tags=tags or []
        )

        # Add to list
        self._entries.append(entry)

        # Trim if needed
        if len(self._entries) > self.max_entries:
            # Keep favorites + most recent
            favorites = [e for e in self._entries if e.favorite]
            non_favorites = [e for e in self._entries if not e.favorite]

            # Keep all favorites + recent non-favorites
            keep_count = self.max_entries - len(favorites)
            self._entries = favorites + non_favorites[-keep_count:]

        # Save to disk
        self._save_history()

        logger.debug(f"Added prompt to history: {prompt[:50]}...")
        return entry

    def get_recent(self, count: int = 10) -> List[PromptEntry]:
        """
        Get most recent prompts.

        Args:
            count: Number of prompts to return

        Returns:
            List of recent PromptEntry objects
        """
        return list(reversed(self._entries[-count:]))

    def get_all(self) -> List[PromptEntry]:
        """Get all prompts (most recent first)."""
        return list(reversed(self._entries))

    def get_favorites(self) -> List[PromptEntry]:
        """Get all favorite prompts."""
        favorites = [e for e in self._entries if e.favorite]
        return list(reversed(favorites))

    def search(self, query: str, case_sensitive: bool = False) -> List[PromptEntry]:
        """
        Search prompts.

        Args:
            query: Search query
            case_sensitive: Whether search is case-sensitive

        Returns:
            List of matching PromptEntry objects
        """
        if not case_sensitive:
            query = query.lower()

        results = []
        for entry in self._entries:
            text = entry.prompt if case_sensitive else entry.prompt.lower()
            if query in text:
                results.append(entry)

        return list(reversed(results))

    def search_by_tag(self, tag: str) -> List[PromptEntry]:
        """
        Search prompts by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of matching PromptEntry objects
        """
        results = [e for e in self._entries if tag in e.tags]
        return list(reversed(results))

    def toggle_favorite(self, prompt: str) -> bool:
        """
        Toggle favorite status of a prompt.

        Args:
            prompt: Prompt text to toggle

        Returns:
            New favorite status
        """
        for entry in self._entries:
            if entry.prompt == prompt:
                entry.favorite = not entry.favorite
                self._save_history()
                return entry.favorite

        logger.warning(f"Prompt not found for favorite toggle: {prompt[:50]}...")
        return False

    def add_tag(self, prompt: str, tag: str) -> bool:
        """
        Add a tag to a prompt.

        Args:
            prompt: Prompt text
            tag: Tag to add

        Returns:
            True if successful
        """
        for entry in self._entries:
            if entry.prompt == prompt:
                if tag not in entry.tags:
                    entry.tags.append(tag)
                    self._save_history()
                return True

        return False

    def remove_tag(self, prompt: str, tag: str) -> bool:
        """
        Remove a tag from a prompt.

        Args:
            prompt: Prompt text
            tag: Tag to remove

        Returns:
            True if successful
        """
        for entry in self._entries:
            if entry.prompt == prompt:
                if tag in entry.tags:
                    entry.tags.remove(tag)
                    self._save_history()
                return True

        return False

    def delete_prompt(self, prompt: str) -> bool:
        """
        Delete a prompt from history.

        Args:
            prompt: Prompt text to delete

        Returns:
            True if deleted
        """
        original_len = len(self._entries)
        self._entries = [e for e in self._entries if e.prompt != prompt]

        if len(self._entries) < original_len:
            self._save_history()
            logger.info(f"Deleted prompt from history: {prompt[:50]}...")
            return True

        return False

    def clear_history(self, keep_favorites: bool = True) -> int:
        """
        Clear history.

        Args:
            keep_favorites: Whether to keep favorite prompts

        Returns:
            Number of entries deleted
        """
        original_count = len(self._entries)

        if keep_favorites:
            self._entries = [e for e in self._entries if e.favorite]
        else:
            self._entries = []

        deleted = original_count - len(self._entries)
        self._save_history()

        logger.info(f"Cleared {deleted} entries from history")
        return deleted

    def export_history(self, export_path: Path) -> None:
        """
        Export history to JSON file.

        Args:
            export_path: Path to export file
        """
        data = {
            "version": "1.0",
            "exported_at": time.time(),
            "entries": [entry.to_dict() for entry in self._entries]
        }

        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(self._entries)} entries to {export_path}")

    def import_history(self, import_path: Path, merge: bool = True) -> int:
        """
        Import history from JSON file.

        Args:
            import_path: Path to import file
            merge: If True, merge with existing history. If False, replace.

        Returns:
            Number of entries imported
        """
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)

            imported_entries = [
                PromptEntry.from_dict(e) for e in data.get("entries", [])
            ]

            if merge:
                # Add imported entries
                self._entries.extend(imported_entries)
                # Remove duplicates (keep most recent)
                seen = set()
                unique_entries = []
                for entry in reversed(self._entries):
                    if entry.prompt not in seen:
                        seen.add(entry.prompt)
                        unique_entries.append(entry)
                self._entries = list(reversed(unique_entries))
            else:
                self._entries = imported_entries

            # Trim if needed
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries:]

            self._save_history()

            logger.info(f"Imported {len(imported_entries)} entries from {import_path}")
            return len(imported_entries)

        except Exception as e:
            logger.error(f"Failed to import history: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get history statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_entries": len(self._entries),
            "favorites": len([e for e in self._entries if e.favorite]),
            "tagged": len([e for e in self._entries if e.tags]),
            "oldest_timestamp": self._entries[0].timestamp if self._entries else None,
            "newest_timestamp": self._entries[-1].timestamp if self._entries else None,
            "unique_tags": len(set(tag for e in self._entries for tag in e.tags)),
        }

    def _load_history(self) -> None:
        """Load history from disk."""
        if not self.history_file.exists():
            logger.debug("No history file found, starting with empty history")
            return

        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)

            self._entries = [
                PromptEntry.from_dict(e) for e in data.get("entries", [])
            ]

            logger.info(f"Loaded {len(self._entries)} entries from history")

        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self._entries = []

    def _save_history(self) -> None:
        """Save history to disk."""
        try:
            data = {
                "version": "1.0",
                "entries": [entry.to_dict() for entry in self._entries]
            }

            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self._entries)} entries to history")

        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None
