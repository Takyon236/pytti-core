"""
Environment compatibility checks for PyTTI Web UI

Detects common dependency issues and provides helpful fixes
"""

import sys
from loguru import logger


def check_numpy_pandas_compatibility():
    """Check for NumPy/pandas binary compatibility issues"""
    try:
        import numpy as np
        numpy_version = np.__version__
        logger.debug(f"NumPy version: {numpy_version}")
    except ImportError:
        logger.error("NumPy is not installed!")
        return False

    try:
        import pandas as pd
        pandas_version = pd.__version__
        logger.debug(f"Pandas version: {pandas_version}")
        return True
    except ValueError as e:
        if "numpy.dtype size changed" in str(e):
            logger.error("=" * 70)
            logger.error("NumPy/Pandas Binary Incompatibility Detected!")
            logger.error("=" * 70)
            logger.error("")
            logger.error("Your pandas library was compiled against a different NumPy version")
            logger.error("than what's currently installed. This causes binary incompatibility.")
            logger.error("")
            logger.error(f"Current NumPy version: {numpy_version}")
            logger.error("")
            logger.error("💡 SOLUTION: Reinstall pandas to match your NumPy version:")
            logger.error("")
            logger.error("    pip uninstall pandas -y")
            logger.error("    pip install pandas --no-cache-dir")
            logger.error("")
            logger.error("Or reinstall all dependencies:")
            logger.error("")
            logger.error("    pip install -c constraints.txt --force-reinstall pandas numpy")
            logger.error("")
            logger.error("=" * 70)
            return False
        else:
            logger.error(f"Error importing pandas: {e}")
            return False
    except Exception as e:
        logger.error(f"Error importing pandas: {e}")
        return False


def check_xformers_compatibility():
    """Check if xformers is compatible with current PyTorch"""
    try:
        import torch
        torch_version = torch.__version__
        logger.debug(f"PyTorch version: {torch_version}")
    except ImportError:
        logger.warning("PyTorch is not installed")
        return True  # Not a blocker for startup

    try:
        import xformers
        xformers_version = xformers.__version__
        logger.debug(f"xformers version: {xformers_version}")

        # Try to actually use xformers
        import xformers.ops
        logger.debug("xformers is available and compatible")
        return True
    except Exception as e:
        logger.warning("=" * 70)
        logger.warning("xformers Incompatibility Detected (non-critical)")
        logger.warning("=" * 70)
        logger.warning("")
        logger.warning("xformers is installed but incompatible with your PyTorch version.")
        logger.warning("The app will work fine without it, just using more VRAM.")
        logger.warning("")
        logger.warning(f"PyTorch version: {torch_version}")
        logger.warning(f"Error: {str(e)[:100]}")
        logger.warning("")
        logger.warning("💡 OPTIONAL FIX (for better performance):")
        logger.warning("")
        logger.warning("    pip uninstall xformers -y")
        logger.warning("    pip install xformers --no-cache-dir")
        logger.warning("")
        logger.warning("Or just leave it - the app works fine without xformers!")
        logger.warning("")
        logger.warning("=" * 70)
        return True  # Not a blocker


def check_environment():
    """
    Run all environment checks

    Returns:
        bool: True if environment is OK, False if critical issues found
    """
    logger.info("Running environment compatibility checks...")

    checks_passed = True

    # Critical check: NumPy/pandas
    if not check_numpy_pandas_compatibility():
        checks_passed = False

    # Non-critical: xformers
    check_xformers_compatibility()

    if checks_passed:
        logger.info("✓ Environment checks passed")
    else:
        logger.error("✗ Critical environment issues detected")
        logger.error("Please fix the issues above before running PyTTI")

    return checks_passed
