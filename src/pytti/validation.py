"""
Input validation for PyTTI.

Validates configuration parameters to prevent crashes and provide helpful errors.
"""

from typing import Dict, Any, List, Tuple
import torch

from pytti.exceptions import InvalidConfigError


class ConfigValidator:
    """
    Validates PyTTI configuration parameters.

    Provides bounds checking, type validation, and helpful error messages.
    """

    # Parameter constraints
    CONSTRAINTS = {
        "width": {"min": 64, "max": 4096, "multiple_of": 8},
        "height": {"min": 64, "max": 4096, "multiple_of": 8},
        "steps_per_scene": {"min": 1, "max": 10000},
        "learning_rate": {"min": 0.0001, "max": 10.0},
        "cutouts": {"min": 1, "max": 256},
        "cut_pow": {"min": 0.1, "max": 10.0},
        "ema_val": {"min": 0.0, "max": 1.0},
        "seed": {"min": -1, "max": 2**32 - 1},
        "save_every": {"min": 1, "max": 10000},
    }

    # Valid model names
    VALID_MODELS = {
        "diffusion": [
            "Stable Diffusion XL",
            "Flux Schnell",
            "Flux Dev",
            "Stable Diffusion 1.5",
        ],
        "clip": [
            "ViT-B/32",
            "ViT-B/16",
            "ViT-L/14",
            "ViT-L/14@336px",
            "SigLIP",
        ],
    }

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate entire configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)

        Example:
            >>> validator = ConfigValidator()
            >>> is_valid, errors = validator.validate_config(config)
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(error)
        """
        errors = []

        # Validate numeric parameters
        for param_name, constraints in cls.CONSTRAINTS.items():
            if param_name in config:
                try:
                    value = config[param_name]
                    error = cls._validate_numeric(param_name, value, constraints)
                    if error:
                        errors.append(error)
                except Exception as e:
                    errors.append(f"{param_name}: {str(e)}")

        # Validate prompt
        if "prompt" in config:
            error = cls._validate_prompt(config["prompt"])
            if error:
                errors.append(error)

        # Validate model selections
        if "diffusion_model" in config:
            error = cls._validate_model(
                "diffusion_model",
                config["diffusion_model"],
                cls.VALID_MODELS["diffusion"]
            )
            if error:
                errors.append(error)

        if "clip_model" in config:
            error = cls._validate_model(
                "clip_model",
                config["clip_model"],
                cls.VALID_MODELS["clip"]
            )
            if error:
                errors.append(error)

        # Validate VRAM requirements
        if "width" in config and "height" in config:
            error = cls._validate_vram_requirements(
                config["width"],
                config["height"],
                config.get("cutouts", 40)
            )
            if error:
                errors.append(error)

        return len(errors) == 0, errors

    @classmethod
    def _validate_numeric(
        cls,
        param_name: str,
        value: Any,
        constraints: Dict[str, Any]
    ) -> str:
        """
        Validate a numeric parameter.

        Returns:
            Error message if invalid, None if valid
        """
        # Type check
        if not isinstance(value, (int, float)):
            return f"{param_name}: must be a number, got {type(value).__name__}"

        # Min check
        if "min" in constraints and value < constraints["min"]:
            return (
                f"{param_name}: {value} is too small "
                f"(minimum: {constraints['min']})"
            )

        # Max check
        if "max" in constraints and value > constraints["max"]:
            return (
                f"{param_name}: {value} is too large "
                f"(maximum: {constraints['max']})"
            )

        # Multiple check
        if "multiple_of" in constraints:
            multiple = constraints["multiple_of"]
            if value % multiple != 0:
                return (
                    f"{param_name}: {value} must be a multiple of {multiple} "
                    f"(try {value - value % multiple} or {value + (multiple - value % multiple)})"
                )

        return None

    @classmethod
    def _validate_prompt(cls, prompt: str) -> str:
        """
        Validate prompt.

        Returns:
            Error message if invalid, None if valid
        """
        if not isinstance(prompt, str):
            return f"prompt: must be a string, got {type(prompt).__name__}"

        if not prompt.strip():
            return "prompt: cannot be empty"

        if len(prompt) > 10000:
            return f"prompt: too long ({len(prompt)} characters, max 10000)"

        # Check for balanced brackets
        bracket_pairs = [("(", ")"), ("[", "]"), ("{", "}")]
        for open_b, close_b in bracket_pairs:
            if prompt.count(open_b) != prompt.count(close_b):
                return (
                    f"prompt: unbalanced brackets "
                    f"(found {prompt.count(open_b)} '{open_b}' "
                    f"but {prompt.count(close_b)} '{close_b}')"
                )

        return None

    @classmethod
    def _validate_model(cls, param_name: str, value: str, valid_models: List[str]) -> str:
        """
        Validate model selection.

        Returns:
            Error message if invalid, None if valid
        """
        if not isinstance(value, str):
            return f"{param_name}: must be a string, got {type(value).__name__}"

        if value not in valid_models:
            return (
                f"{param_name}: '{value}' is not a valid model. "
                f"Valid options: {', '.join(valid_models)}"
            )

        return None

    @classmethod
    def _validate_vram_requirements(
        cls,
        width: int,
        height: int,
        cutouts: int
    ) -> str:
        """
        Validate VRAM requirements.

        Returns:
            Warning message if VRAM might be insufficient, None if okay
        """
        if not torch.cuda.is_available():
            # CPU mode - no VRAM checks
            return None

        try:
            # Get available VRAM
            total_vram_mb = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024

            # Rough estimate of VRAM needed
            # Base model: ~6GB for SDXL, ~3GB for SD1.5
            # + Image size overhead: width * height * cutouts * 0.00001 MB
            base_vram = 6000  # MB (SDXL estimate)
            image_vram = (width * height * cutouts) * 0.00001

            estimated_vram = base_vram + image_vram

            if estimated_vram > total_vram_mb:
                return (
                    f"⚠️ Warning: This configuration may require ~{estimated_vram:.0f}MB VRAM, "
                    f"but you have {total_vram_mb:.0f}MB. "
                    f"Consider reducing image size or cutouts."
                )

            # Also warn if using >90% of VRAM
            if estimated_vram > total_vram_mb * 0.9:
                return (
                    f"⚠️ Warning: This configuration will use ~{estimated_vram:.0f}MB "
                    f"of your {total_vram_mb:.0f}MB VRAM. "
                    f"You may experience slowdowns or crashes."
                )

        except Exception:
            # If we can't check VRAM, don't fail validation
            pass

        return None

    @classmethod
    def validate_and_raise(cls, config: Dict[str, Any]) -> None:
        """
        Validate configuration and raise exception if invalid.

        Args:
            config: Configuration dictionary

        Raises:
            InvalidConfigError: If configuration is invalid

        Example:
            >>> ConfigValidator.validate_and_raise(config)
            >>> # If we get here, config is valid
        """
        is_valid, errors = cls.validate_config(config)

        if not is_valid:
            error_message = "\n".join(f"  • {error}" for error in errors)
            raise InvalidConfigError(
                param_name="multiple",
                param_value="see details",
                reason=f"Configuration validation failed:\n{error_message}"
            )

    @classmethod
    def get_safe_value(cls, param_name: str, value: Any) -> Any:
        """
        Get a safe value for a parameter, clamping if needed.

        Args:
            param_name: Parameter name
            value: Input value

        Returns:
            Safe value (clamped to valid range)

        Example:
            >>> safe_width = ConfigValidator.get_safe_value("width", 5000)
            >>> # Returns 4096 (max allowed width)
        """
        if param_name not in cls.CONSTRAINTS:
            return value

        constraints = cls.CONSTRAINTS[param_name]

        # Clamp to min
        if "min" in constraints:
            value = max(value, constraints["min"])

        # Clamp to max
        if "max" in constraints:
            value = min(value, constraints["max"])

        # Round to multiple
        if "multiple_of" in constraints:
            multiple = constraints["multiple_of"]
            value = round(value / multiple) * multiple

        return value
