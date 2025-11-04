#!/usr/bin/env python3
"""
PyTTI Modern - Installation Validation Script

Run this script to verify your PyTTI installation and check which modern
features are available.

Usage:
    python validate_installation.py
    python validate_installation.py --verbose
    python validate_installation.py --test-models  # Actually load models (takes time)
"""

import sys
import argparse
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")

def print_error(text):
    print(f"{Colors.RED}✗{Colors.RESET} {text}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {text}")


def check_python_version():
    """Check Python version"""
    print_header("Python Version")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major >= 3 and version.minor >= 10:
        print_success(f"Python {version_str} (Required: 3.10+)")
        return True
    else:
        print_error(f"Python {version_str} (Required: 3.10+)")
        print_info("  Please upgrade to Python 3.10 or higher")
        return False


def check_core_dependencies():
    """Check core PyTTI dependencies"""
    print_header("Core Dependencies")

    deps = {
        "torch": "PyTorch",
        "torchvision": "TorchVision",
        "PIL": "Pillow (PIL)",
        "numpy": "NumPy",
        "omegaconf": "OmegaConf",
        "hydra": "Hydra",
        "loguru": "Loguru",
    }

    all_ok = True
    for module_name, display_name in deps.items():
        try:
            if module_name == "PIL":
                import PIL
                version = PIL.__version__
            else:
                module = __import__(module_name)
                version = getattr(module, "__version__", "unknown")

            print_success(f"{display_name}: {version}")
        except ImportError:
            print_error(f"{display_name}: Not installed")
            all_ok = False

    return all_ok


def check_pytorch_cuda():
    """Check PyTorch CUDA support"""
    print_header("PyTorch & CUDA")

    try:
        import torch

        print_success(f"PyTorch version: {torch.__version__}")

        if torch.cuda.is_available():
            print_success(f"CUDA available: {torch.cuda.get_device_name(0)}")
            print_info(f"  CUDA version: {torch.version.cuda}")
            print_info(f"  Device count: {torch.cuda.device_count()}")

            # Check memory
            memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print_info(f"  GPU memory: {memory_gb:.1f} GB")

            if memory_gb < 8:
                print_warning("  Low GPU memory. Consider using fp16 and smaller models")
            elif memory_gb < 12:
                print_info("  Good GPU memory for SDXL at 1024x1024")
            else:
                print_success("  Excellent GPU memory for large models")

            return True
        else:
            print_warning("CUDA not available - CPU mode only")
            print_info("  Install CUDA-enabled PyTorch for GPU acceleration")
            return False

    except ImportError:
        print_error("PyTorch not installed")
        return False


def check_modern_dependencies():
    """Check modern PyTTI dependencies"""
    print_header("Modern AI Dependencies")

    deps = {
        "diffusers": ("Diffusers", "For Stable Diffusion/Flux support"),
        "transformers": ("Transformers", "For modern CLIP and depth models"),
        "accelerate": ("Accelerate", "For multi-GPU and optimization"),
        "safetensors": ("SafeTensors", "For safe model loading"),
    }

    all_ok = True
    for module_name, (display_name, purpose) in deps.items():
        try:
            module = __import__(module_name)
            version = getattr(module, "__version__", "unknown")
            print_success(f"{display_name}: {version}")
            print_info(f"  → {purpose}")
        except ImportError:
            print_error(f"{display_name}: Not installed")
            print_info(f"  → {purpose}")
            print_info(f"  Install with: pip install {module_name}")
            all_ok = False

    return all_ok


def check_optional_dependencies():
    """Check optional dependencies"""
    print_header("Optional Dependencies")

    # SAM 2 for AI rotoscoping
    try:
        import sam2
        print_success(f"SAM 2: Available (AI rotoscoping enabled)")
    except ImportError:
        print_warning("SAM 2: Not installed (AI rotoscoping disabled)")
        print_info("  Install with: pip install git+https://github.com/facebookresearch/segment-anything-2.git")

    # xformers for memory efficiency
    try:
        import xformers
        print_success(f"xformers: {xformers.__version__} (Memory optimization enabled)")
    except ImportError:
        print_warning("xformers: Not installed (Memory optimization disabled)")
        print_info("  Install with: pip install xformers")

    # Legacy AdaBins
    try:
        import adabins
        print_success("AdaBins: Available (Legacy depth model)")
    except ImportError:
        print_info("AdaBins: Not installed (Legacy depth - not needed)")


def check_pytti_installation():
    """Check PyTTI installation"""
    print_header("PyTTI Installation")

    try:
        import pytti
        print_success("PyTTI core: Installed")

        # Check for modern modules
        try:
            from pytti.model_loader import ModelRegistry
            print_success("  Modern model loader: Available")

            # Count available models
            from pytti.model_loader import ModelType
            diffusion_count = len(ModelRegistry.list_models_by_type(ModelType.DIFFUSION))
            depth_count = len(ModelRegistry.list_models_by_type(ModelType.DEPTH))
            seg_count = len(ModelRegistry.list_models_by_type(ModelType.SEGMENTATION))

            print_info(f"  Available models:")
            print_info(f"    - Diffusion: {diffusion_count}")
            print_info(f"    - Depth: {depth_count}")
            print_info(f"    - Segmentation: {seg_count}")

        except ImportError:
            print_warning("  Modern model loader: Not available")

        # Check for modern image models
        try:
            from pytti.image_models import DIFFUSION_AVAILABLE
            if DIFFUSION_AVAILABLE:
                print_success("  Modern diffusion models: Available")
            else:
                print_warning("  Modern diffusion models: Not available")
        except ImportError:
            print_warning("  Modern diffusion models: Not available")

        # Check for modern depth
        try:
            from pytti.depth_models import DepthAnythingV2
            print_success("  Modern depth estimation: Available")
        except ImportError:
            print_warning("  Modern depth estimation: Not available")

        # Check for AI rotoscoping
        try:
            from pytti.rotoscoper_v2 import AIRotoscoper
            print_success("  AI rotoscoping: Available")
        except ImportError:
            print_warning("  AI rotoscoping: Not available")

        return True

    except ImportError:
        print_error("PyTTI core: Not installed")
        print_info("  Install with: pip install -e .")
        return False


def test_model_loading(verbose=False):
    """Actually test loading models (optional, takes time)"""
    print_header("Model Loading Tests (This may take a few minutes)")

    import torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Test diffusion model loading
    try:
        from pytti.model_loader import get_model_loader
        print_info("Testing SDXL loading...")

        loader = get_model_loader(device=device)
        pipe = loader.load_diffusion_model("sdxl", variant="fp16" if device.type == "cuda" else None)

        print_success("SDXL model: Loaded successfully")

        loader.unload_model("sdxl")
        torch.cuda.empty_cache() if device.type == "cuda" else None

    except Exception as e:
        print_error(f"SDXL model: Failed to load")
        if verbose:
            print(f"  Error: {e}")

    # Test depth model loading
    try:
        from pytti.depth_models import init_depth_model
        print_info("Testing Depth-Anything-V2 loading...")

        init_depth_model("depth_anything_v2", "small", device=device)
        print_success("Depth-Anything-V2: Loaded successfully")

    except Exception as e:
        print_error(f"Depth-Anything-V2: Failed to load")
        if verbose:
            print(f"  Error: {e}")


def print_summary(results):
    """Print summary of validation"""
    print_header("Validation Summary")

    python_ok, core_ok, cuda_ok, modern_ok, pytti_ok = results

    if all(results[:3]):  # Python, core, PyTTI
        print_success("PyTTI core installation: READY")
    else:
        print_error("PyTTI core installation: INCOMPLETE")

    if modern_ok:
        print_success("Modern AI features: READY")
    else:
        print_warning("Modern AI features: PARTIALLY AVAILABLE")

    if cuda_ok:
        print_success("GPU acceleration: ENABLED")
    else:
        print_warning("GPU acceleration: DISABLED (CPU only)")

    print()

    # Recommendations
    if not all(results):
        print_info("Recommendations:")

        if not core_ok:
            print_info("  1. Install core dependencies: pip install -r requirements.txt")

        if not modern_ok:
            print_info("  2. Install modern dependencies: pip install -r requirements-modern.txt")

        if not pytti_ok:
            print_info("  3. Install PyTTI: pip install -e .")

        if not cuda_ok:
            print_info("  4. Install CUDA-enabled PyTorch for GPU support")

    else:
        print_success("All systems ready! Try running:")
        print_info("  python -m pytti.workhorse preset=sdxl_default scenes=\"your prompt\"")


def main():
    parser = argparse.ArgumentParser(description="Validate PyTTI installation")
    parser.add_argument("--verbose", action="store_true", help="Show detailed error messages")
    parser.add_argument("--test-models", action="store_true", help="Actually test loading models (slow)")
    args = parser.parse_args()

    print(f"{Colors.BOLD}PyTTI Modern - Installation Validator{Colors.RESET}")
    print("This script checks if PyTTI and its modern dependencies are properly installed.\n")

    # Run checks
    python_ok = check_python_version()
    core_ok = check_core_dependencies()
    cuda_ok = check_pytorch_cuda()
    modern_ok = check_modern_dependencies()
    check_optional_dependencies()
    pytti_ok = check_pytti_installation()

    if args.test_models and pytti_ok and modern_ok:
        test_model_loading(verbose=args.verbose)

    # Summary
    print_summary([python_ok, core_ok, cuda_ok, modern_ok, pytti_ok])

    # Exit code
    if all([python_ok, core_ok, pytti_ok]):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
