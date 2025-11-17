# Python Version Compatibility Guide

## Quick Diagnosis

If you're getting this error:
```
RuntimeError: operator torchvision::nms does not exist
```

**You're likely using Python 3.12 with incompatible PyTorch versions.**

## Recommended Solution

### Option 1: Use Python 3.10 or 3.11 (RECOMMENDED)

This is the most stable approach as it matches the tested configuration:

```bash
# Create new conda environment with Python 3.11
conda create -n pytti python=3.11
conda activate pytti

# Navigate to pytti-core directory
cd /path/to/pytti-core

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Option 2: Use Python 3.12 with Updated Dependencies

If you must use Python 3.12:

```bash
# Use the Python 3.12 compatible requirements
pip install -r requirements-py312.txt
pip install -e .
```

**Warning:** Python 3.12 support is newer and less tested. You may encounter other compatibility issues.

## About xformers

If you see errors about `xformers`:

1. **Don't install xformers unless you specifically need it** - it's optional
2. If you do need it, install the version matching your CUDA and PyTorch:
   ```bash
   # For CUDA 11.8 and torch 2.1+
   pip install xformers>=0.0.22
   ```
3. If xformers installation breaks things, uninstall it:
   ```bash
   pip uninstall xformers
   ```

## Supported Python Versions

| Python Version | Status | PyTorch Version | Notes |
|----------------|--------|----------------|-------|
| 3.10 | ✅ Fully Supported | 1.13.1 | Recommended |
| 3.11 | ✅ Fully Supported | 1.13.1 | Recommended |
| 3.12 | ⚠️ Requires Updates | 2.1.0+ | Use requirements-py312.txt |
| 3.13+ | ❌ Not Supported | - | Too new |

## Troubleshooting

### "RuntimeError: operator torchvision::nms does not exist"
- **Cause:** PyTorch/torchvision version incompatible with your Python version
- **Fix:** Use Python 3.10 or 3.11, or upgrade PyTorch (see above)

### "ModuleNotFoundError: No module named 'xformers'"
- **Cause:** Code trying to import optional xformers
- **Fix:** Either install xformers or ignore (it's optional)

### "ImportError: cannot import name 'xxx' from 'torchvision'"
- **Cause:** Version mismatch between torch and torchvision
- **Fix:** Reinstall matching versions:
  ```bash
  pip install torch==1.13.1 torchvision==0.14.1  # For Python 3.10/3.11
  # OR
  pip install torch>=2.1.0 torchvision>=0.16.0   # For Python 3.12
  ```

## Clean Installation (Reset Everything)

If you're stuck in dependency hell:

```bash
# Remove existing environment
conda deactivate
conda env remove -n pytti

# Create fresh environment with correct Python version
conda create -n pytti python=3.11
conda activate pytti

# Clean pip cache
pip cache purge

# Install fresh
cd /path/to/pytti-core
pip install -r requirements.txt
pip install -e .
```

## Why These Errors Happen

The original `requirements.txt` was created for Python 3.10/3.11 with:
- `torch==1.13.1` (January 2023)
- `torchvision==0.14.1` (January 2023)

Python 3.12 was released **October 2023**, after these PyTorch versions. The old PyTorch C++ extensions don't work with Python 3.12's updated C API.

Solution: Either use older Python (stable) or newer PyTorch (experimental).
