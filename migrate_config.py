#!/usr/bin/env python3
"""
PyTTI Config Migration Tool

Automatically converts old PyTTI configs to modern format.
Helps users migrate from VQGAN/AdaBins to SDXL/Depth-Anything-V2.

Usage:
    python migrate_config.py old_config.yaml
    python migrate_config.py old_config.yaml --output new_config.yaml
    python migrate_config.py old_config.yaml --model sdxl  # Choose specific model
    python migrate_config.py old_config.yaml --dry-run     # Preview changes
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)


class ConfigMigrator:
    """Migrates old PyTTI configs to modern format"""

    # Model mappings
    IMAGE_MODEL_MAP = {
        "VQGAN": "Stable Diffusion XL",  # Default modern replacement
        "Limited Palette": "Limited Palette",  # Keep as-is
        "Unlimited Palette": "Unlimited Palette",  # Keep as-is
    }

    VQGAN_TO_DIFFUSION = {
        "imagenet": "sdxl",
        "coco": "sdxl",
        "wikiart": "sdxl",  # SDXL is versatile
        "sflckr": "sdxl",
        "openimages": "sdxl",
    }

    def __init__(self, prefer_model: str = "sdxl"):
        """
        Initialize migrator

        Args:
            prefer_model: Preferred modern model (sdxl, flux_schnell, sd_1.5)
        """
        self.prefer_model = prefer_model
        self.changes = []

    def migrate(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate old config to new format

        Args:
            old_config: Old configuration dictionary

        Returns:
            New configuration dictionary
        """
        new_config = old_config.copy()
        self.changes = []

        # 1. Migrate image model
        self._migrate_image_model(new_config)

        # 2. Migrate depth settings
        self._migrate_depth_settings(new_config)

        # 3. Migrate dimensions (suggest larger for modern models)
        self._migrate_dimensions(new_config)

        # 4. Add modern performance settings
        self._add_modern_settings(new_config)

        # 5. Clean up obsolete settings
        self._cleanup_obsolete(new_config)

        return new_config

    def _migrate_image_model(self, config: Dict[str, Any]):
        """Migrate image_model setting"""
        old_model = config.get("image_model", "VQGAN")

        if old_model == "VQGAN":
            # Map VQGAN model to modern equivalent
            vqgan_model = config.get("vqgan_model", "sflckr")
            new_model_id = self.VQGAN_TO_DIFFUSION.get(vqgan_model, "sdxl")

            if self.prefer_model == "sdxl":
                config["image_model"] = "Stable Diffusion XL"
                config["diffusion_model_id"] = "sdxl"
            elif self.prefer_model == "flux_schnell":
                config["image_model"] = "Flux Schnell"
                config["diffusion_model_id"] = "flux_schnell"
            elif self.prefer_model == "flux_dev":
                config["image_model"] = "Flux Dev"
                config["diffusion_model_id"] = "flux_dev"
            else:
                config["image_model"] = "Stable Diffusion XL"
                config["diffusion_model_id"] = "sdxl"

            self.changes.append(
                f"image_model: {old_model} (vqgan_model: {vqgan_model}) → {config['image_model']}"
            )

        elif old_model in ["Limited Palette", "Unlimited Palette"]:
            # Keep legacy models as-is
            self.changes.append(f"image_model: {old_model} (kept unchanged)")

    def _migrate_depth_settings(self, config: Dict[str, Any]):
        """Add modern depth settings"""
        if "depth_model" not in config:
            config["depth_model"] = "depth_anything_v2"
            config["depth_model_size"] = "base"
            self.changes.append("Added: depth_model = depth_anything_v2 (replaces AdaBins)")

    def _migrate_dimensions(self, config: Dict[str, Any]):
        """Suggest larger dimensions for modern models"""
        old_width = config.get("width", 180)
        old_height = config.get("height", 112)

        # If using small dimensions and modern model, suggest upgrade
        if config.get("image_model") in ["Stable Diffusion XL", "Flux Schnell", "Flux Dev"]:
            if old_width < 512 or old_height < 512:
                # Suggest 1024x1024 for SDXL/Flux
                config["width"] = 1024
                config["height"] = 1024
                self.changes.append(
                    f"dimensions: {old_width}x{old_height} → 1024x1024 "
                    "(modern models work better at higher resolution)"
                )

    def _add_modern_settings(self, config: Dict[str, Any]):
        """Add modern performance settings"""
        modern_settings = {
            "use_modern_clip": True,
            "clip_model": "siglip",
            "use_fp16": True,
            "enable_xformers": True,
        }

        for key, value in modern_settings.items():
            if key not in config:
                config[key] = value
                self.changes.append(f"Added: {key} = {value}")

    def _cleanup_obsolete(self, config: Dict[str, Any]):
        """Remove obsolete settings"""
        obsolete_keys = [
            "ViTB32", "ViTB16", "ViTL14",  # Old CLIP settings
            "RN50", "RN101", "RN50x4", "RN50x16", "RN50x64",
        ]

        for key in obsolete_keys:
            if key in config:
                del config[key]
                self.changes.append(f"Removed obsolete: {key}")

    def print_changes(self):
        """Print summary of changes"""
        if not self.changes:
            print("No changes needed - config is already modern!")
            return

        print("\nMigration Changes:")
        print("=" * 60)
        for i, change in enumerate(self.changes, 1):
            print(f"{i}. {change}")
        print("=" * 60)


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML config file"""
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in config file: {e}")
        sys.exit(1)


def save_yaml(config: Dict[str, Any], path: Path):
    """Save YAML config file"""
    try:
        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"\nSaved migrated config to: {path}")
    except Exception as e:
        print(f"Error: Failed to save config: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate old PyTTI configs to modern format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate to SDXL (recommended)
  python migrate_config.py old_config.yaml

  # Migrate to Flux
  python migrate_config.py old_config.yaml --model flux_schnell

  # Preview changes without saving
  python migrate_config.py old_config.yaml --dry-run

  # Save to specific output file
  python migrate_config.py old_config.yaml --output new_config.yaml
        """
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to old config file"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output path for migrated config (default: <input>_modern.yaml)"
    )
    parser.add_argument(
        "--model", "-m",
        choices=["sdxl", "flux_schnell", "flux_dev", "sd_1.5"],
        default="sdxl",
        help="Preferred modern model (default: sdxl)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview changes without saving"
    )
    parser.add_argument(
        "--backup", "-b",
        action="store_true",
        help="Create backup of original config"
    )

    args = parser.parse_args()

    # Load old config
    print(f"Loading config from: {args.config}")
    old_config = load_yaml(args.config)

    # Migrate
    print(f"Migrating to modern format (target model: {args.model})")
    migrator = ConfigMigrator(prefer_model=args.model)
    new_config = migrator.migrate(old_config)

    # Show changes
    migrator.print_changes()

    if not migrator.changes:
        return

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = args.config.parent / f"{args.config.stem}_modern.yaml"

    # Save (unless dry-run)
    if args.dry_run:
        print("\nDry run - no files modified")
        print(f"Would save to: {output_path}")
    else:
        # Backup original if requested
        if args.backup:
            backup_path = args.config.parent / f"{args.config.stem}_backup.yaml"
            import shutil
            shutil.copy2(args.config, backup_path)
            print(f"Backed up original to: {backup_path}")

        # Save migrated config
        save_yaml(new_config, output_path)

        print("\nMigration complete!")
        print(f"\nTo use the new config:")
        print(f"  python -m pytti.workhorse --config-name {output_path.stem}")


if __name__ == "__main__":
    main()
