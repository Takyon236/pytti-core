"""
Custom exceptions for PyTTI.

Provides user-friendly error messages and better error categorization.
"""

from typing import Any


class PyTTIException(Exception):
    """Base exception for all PyTTI errors."""

    def __init__(self, message: str, user_message: str = None, details: str = None):
        """
        Initialize PyTTI exception.

        Args:
            message: Technical error message (for logs)
            user_message: User-friendly error message (for UI display)
            details: Additional details or suggestions
        """
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message
        self.details = details

    def get_user_message(self) -> str:
        """Get formatted user-friendly error message."""
        msg = self.user_message
        if self.details:
            msg += f"\n\n{self.details}"
        return msg


class ModelLoadError(PyTTIException):
    """Error loading AI models."""

    def __init__(self, model_name: str, original_error: Exception = None):
        message = f"Failed to load model: {model_name}"
        user_message = f"Could not load the AI model '{model_name}'"

        details = None
        if original_error:
            error_str = str(original_error).lower()

            if "out of memory" in error_str or "oom" in error_str:
                details = (
                    "💡 Suggestions:\n"
                    "• Try a smaller image size (e.g., 512x512 instead of 1024x1024)\n"
                    "• Close other applications using GPU memory\n"
                    "• Restart the application to clear GPU cache"
                )
            elif "connection" in error_str or "timeout" in error_str:
                details = (
                    "💡 Suggestions:\n"
                    "• Check your internet connection\n"
                    "• The model download may have been interrupted\n"
                    "• Try again in a few moments"
                )
            elif "permission" in error_str or "access" in error_str:
                details = (
                    "💡 Suggestions:\n"
                    "• Check file permissions in the cache directory\n"
                    "• Run with appropriate permissions\n"
                    "• Check disk space"
                )
            else:
                details = f"Technical details: {str(original_error)}"

        super().__init__(message, user_message, details)
        self.model_name = model_name
        self.original_error = original_error


class CLIPNotInitializedError(PyTTIException):
    """CLIP models not initialized."""

    def __init__(self):
        message = "CLIP models not initialized"
        user_message = "CLIP vision model is not loaded"
        details = (
            "💡 This is an internal error. The application should initialize CLIP automatically.\n"
            "Please report this as a bug if you see this message."
        )
        super().__init__(message, user_message, details)


class InvalidConfigError(PyTTIException):
    """Invalid configuration parameters."""

    def __init__(self, param_name: str, param_value: Any, reason: str):
        from typing import Any

        message = f"Invalid config parameter '{param_name}': {reason}"
        user_message = f"Invalid setting: {param_name}"
        details = f"Value '{param_value}' is invalid: {reason}"
        super().__init__(message, user_message, details)
        self.param_name = param_name
        self.param_value = param_value


class VRAMError(PyTTIException):
    """GPU memory (VRAM) errors."""

    def __init__(self, required_mb: float = None, available_mb: float = None):
        if required_mb and available_mb:
            message = f"Insufficient VRAM: need {required_mb:.0f}MB, have {available_mb:.0f}MB"
            user_message = "Not enough GPU memory"
            details = (
                f"Required: {required_mb:.0f} MB\n"
                f"Available: {available_mb:.0f} MB\n\n"
                "💡 Suggestions:\n"
                "• Reduce image size (try 512x512 or 768x768)\n"
                "• Reduce number of cutouts\n"
                "• Close other GPU applications\n"
                "• Restart to clear GPU cache"
            )
        else:
            message = "GPU out of memory"
            user_message = "Not enough GPU memory"
            details = (
                "💡 Suggestions:\n"
                "• Reduce image size\n"
                "• Reduce number of cutouts\n"
                "• Close other GPU applications\n"
                "• Restart the application"
            )

        super().__init__(message, user_message, details)
        self.required_mb = required_mb
        self.available_mb = available_mb


class GenerationError(PyTTIException):
    """Error during image generation."""

    def __init__(self, step: int, original_error: Exception):
        message = f"Generation failed at step {step}: {str(original_error)}"
        user_message = f"Image generation failed at step {step}"
        details = f"Error: {str(original_error)}"
        super().__init__(message, user_message, details)
        self.step = step
        self.original_error = original_error


class PromptParseError(PyTTIException):
    """Error parsing prompt."""

    def __init__(self, prompt: str, original_error: Exception = None):
        message = f"Failed to parse prompt: {prompt}"
        user_message = "Could not understand the prompt"
        details = (
            f"Prompt: {prompt}\n\n"
            "💡 Suggestions:\n"
            "• Check for balanced brackets and quotes\n"
            "• Remove special characters if present\n"
            "• Try a simpler prompt first"
        )
        if original_error:
            details += f"\n\nTechnical details: {str(original_error)}"

        super().__init__(message, user_message, details)
        self.prompt = prompt
        self.original_error = original_error


class FileIOError(PyTTIException):
    """File input/output errors."""

    def __init__(self, operation: str, path: str, original_error: Exception):
        message = f"File {operation} failed: {path}"
        user_message = f"Could not {operation} file"
        details = (
            f"Path: {path}\n"
            f"Error: {str(original_error)}\n\n"
            "💡 Suggestions:\n"
            "• Check file permissions\n"
            "• Check available disk space\n"
            "• Verify the path exists and is writable"
        )
        super().__init__(message, user_message, details)
        self.operation = operation
        self.path = path
        self.original_error = original_error
