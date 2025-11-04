"""
Logging Configuration for PyTTI

Provides structured, rotating logs with different levels for console and file output.
Includes performance timing decorators and context managers.
"""

import sys
import time
from pathlib import Path
from typing import Optional, Callable, Any
from functools import wraps
from contextlib import contextmanager

from loguru import logger


def setup_logging(
    log_dir: Optional[Path] = None,
    log_level: str = "INFO",
    console_level: str = "INFO",
    enable_rotation: bool = True,
) -> None:
    """
    Configure logging for PyTTI.

    Sets up console and file logging with rotation and formatting.

    Args:
        log_dir: Directory for log files (defaults to ~/. pytti/logs)
        log_level: File logging level (DEBUG, INFO, WARNING, ERROR)
        console_level: Console logging level
        enable_rotation: Enable log file rotation

    Example:
        >>> setup_logging(log_level="DEBUG")
        >>> logger.info("Logging configured!")
    """
    # Remove default handler
    logger.remove()

    # Create log directory
    if log_dir is None:
        log_dir = Path.home() / ".pytti" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)

    # ========================================
    # Console Handler (colored, human-readable)
    # ========================================
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        format=console_format,
        level=console_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # ========================================
    # File Handler (detailed, structured)
    # ========================================
    if enable_rotation:
        # Main log file with rotation
        logger.add(
            log_dir / "pytti.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level=log_level,
            rotation="10 MB",  # Rotate when file reaches 10MB
            retention="7 days",  # Keep logs for 7 days
            compression="zip",  # Compress rotated logs
            backtrace=True,
            diagnose=True,
        )

        # Error log (errors only)
        logger.add(
            log_dir / "pytti_errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
            level="ERROR",
            rotation="5 MB",
            retention="30 days",  # Keep error logs longer
            compression="zip",
            backtrace=True,
            diagnose=True,
        )

    logger.info(f"Logging configured: {log_dir}")
    logger.info(f"  Console level: {console_level}")
    logger.info(f"  File level: {log_level}")
    logger.info(f"  Rotation: {'enabled' if enable_rotation else 'disabled'}")


def timing_decorator(func: Callable) -> Callable:
    """
    Decorator to log function execution time.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function

    Example:
        >>> @timing_decorator
        ... def slow_function():
        ...     time.sleep(1)
        >>> slow_function()  # Logs: "slow_function took 1.00s"
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        logger.debug(f"{func.__name__} took {elapsed:.2f}s")

        return result

    return wrapper


@contextmanager
def log_context(name: str, level: str = "INFO"):
    """
    Context manager for logging entry/exit of code blocks.

    Args:
        name: Name of the context
        level: Log level

    Example:
        >>> with log_context("Model Loading"):
        ...     load_model()
        # Logs: "→ Entering Model Loading"
        # Logs: "← Exiting Model Loading (took 2.34s)"
    """
    start = time.time()

    if level == "DEBUG":
        logger.debug(f"→ Entering {name}")
    elif level == "INFO":
        logger.info(f"→ Entering {name}")
    elif level == "WARNING":
        logger.warning(f"→ Entering {name}")
    elif level == "ERROR":
        logger.error(f"→ Entering {name}")

    try:
        yield
    finally:
        elapsed = time.time() - start

        if level == "DEBUG":
            logger.debug(f"← Exiting {name} (took {elapsed:.2f}s)")
        elif level == "INFO":
            logger.info(f"← Exiting {name} (took {elapsed:.2f}s)")
        elif level == "WARNING":
            logger.warning(f"← Exiting {name} (took {elapsed:.2f}s)")
        elif level == "ERROR":
            logger.error(f"← Exiting {name} (took {elapsed:.2f}s)")


class PerformanceLogger:
    """
    Logger for performance metrics.

    Tracks timing, memory usage, and other performance metrics.

    Example:
        >>> perf = PerformanceLogger()
        >>> perf.start("generation")
        >>> # ... do work ...
        >>> perf.end("generation")
        >>> perf.log_summary()
    """

    def __init__(self):
        """Initialize performance logger."""
        self.timings: dict[str, list[float]] = {}
        self.active: dict[str, float] = {}

    def start(self, name: str) -> None:
        """
        Start timing an operation.

        Args:
            name: Operation name
        """
        self.active[name] = time.time()

    def end(self, name: str) -> float:
        """
        End timing an operation.

        Args:
            name: Operation name

        Returns:
            Elapsed time in seconds
        """
        if name not in self.active:
            logger.warning(f"Cannot end timing for '{name}' - never started")
            return 0.0

        elapsed = time.time() - self.active[name]
        del self.active[name]

        if name not in self.timings:
            self.timings[name] = []
        self.timings[name].append(elapsed)

        return elapsed

    def log_summary(self) -> None:
        """Log summary of all timing data."""
        if not self.timings:
            logger.info("No performance data to log")
            return

        logger.info("=" * 60)
        logger.info("📊 PERFORMANCE SUMMARY")
        logger.info("=" * 60)

        for name, times in self.timings.items():
            total = sum(times)
            avg = total / len(times)
            min_time = min(times)
            max_time = max(times)

            logger.info(f"  {name}:")
            logger.info(f"    Count: {len(times)}")
            logger.info(f"    Total: {total:.2f}s")
            logger.info(f"    Average: {avg:.2f}s")
            logger.info(f"    Min: {min_time:.2f}s")
            logger.info(f"    Max: {max_time:.2f}s")

        logger.info("=" * 60)

    def reset(self) -> None:
        """Reset all timing data."""
        self.timings.clear()
        self.active.clear()


# Global performance logger instance
_perf_logger = PerformanceLogger()


def get_performance_logger() -> PerformanceLogger:
    """
    Get global performance logger instance.

    Returns:
        PerformanceLogger instance
    """
    return _perf_logger


# Convenience functions

def log_vram_usage(label: str = "") -> None:
    """
    Log current VRAM usage.

    Args:
        label: Optional label for the log message
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return

        allocated = torch.cuda.memory_allocated() / 1024 / 1024  # MB
        reserved = torch.cuda.memory_reserved() / 1024 / 1024  # MB
        total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024  # MB

        prefix = f"{label}: " if label else ""
        logger.debug(
            f"{prefix}VRAM: {allocated:.0f}MB allocated, "
            f"{reserved:.0f}MB reserved, {total:.0f}MB total"
        )

    except Exception as e:
        logger.warning(f"Failed to log VRAM usage: {e}")


def log_system_info() -> None:
    """Log system information."""
    import platform
    import torch

    logger.info("=" * 60)
    logger.info("💻 SYSTEM INFORMATION")
    logger.info("=" * 60)
    logger.info(f"  Platform: {platform.system()} {platform.release()}")
    logger.info(f"  Python: {platform.python_version()}")
    logger.info(f"  PyTorch: {torch.__version__}")

    if torch.cuda.is_available():
        logger.info(f"  CUDA: {torch.version.cuda}")
        logger.info(f"  GPU: {torch.cuda.get_device_name(0)}")
        memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"  VRAM: {memory_gb:.1f} GB")
    else:
        logger.info("  GPU: Not available (CPU mode)")

    logger.info("=" * 60)
