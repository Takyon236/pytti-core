# Python Version Compatibility

## Quick Start

**Python 3.10, 3.11, or 3.12 are all fully supported.**

```bash
# Create environment with your preferred Python version
conda create -n pytti python=3.12  # or 3.11, or 3.10
conda activate pytti

# Install
cd /path/to/pytti-core
pip install -r requirements.txt
pip install -e .

# Run
pytti-webui
```

## Supported Python Versions

| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.10 | ✅ Fully Supported | Stable |
| 3.11 | ✅ Fully Supported | Stable |
| 3.12 | ✅ Fully Supported | Modern, recommended |
| 3.13+ | ❌ Not Tested | May work but untested |

## Common Errors and Fixes

### "RuntimeError: operator torchvision::nms does not exist"

**Cause:** Old PyTorch version installed (likely torch < 2.1.0)

**Fix:**
```bash
# Uninstall old versions
pip uninstall torch torchvision -y

# Reinstall from requirements
pip install -r requirements.txt
```

### "ModuleNotFoundError: No module named 'xformers'"

**Cause:** Code trying to import optional xformers library

**Fix:** xformers is **completely optional** and often causes problems. You don't need it.

If you want to try it anyway:
```bash
pip install xformers>=0.0.22
```

If it breaks things, remove it:
```bash
pip uninstall xformers
```

### "ImportError: cannot import name 'xxx' from 'torchvision'"

**Cause:** Mismatched torch/torchvision versions

**Fix:**
```bash
# Clean reinstall
pip uninstall torch torchvision -y
pip install -r requirements.txt
```

## Clean Installation (Reset Everything)

If you're stuck in dependency hell:

```bash
# Remove existing environment
conda deactivate
conda env remove -n pytti

# Create fresh environment
conda create -n pytti python=3.12
conda activate pytti

# Clean pip cache
pip cache purge

# Install fresh
cd /path/to/pytti-core
pip install -r requirements.txt
pip install -e .

# Test
pytti-webui
```

## What Changed

The original `requirements.txt` used ancient dependencies:
- `torch==1.13.1` (January 2023)
- `Pillow==7.1` (March 2020!)
- `imageio==2.4.1` (January 2018!)

These don't work with Python 3.12 and have security/bug issues.

**New requirements.txt uses modern versions:**
- `torch>=2.1.0` (Python 3.12 support)
- `Pillow>=10.0.0` (current stable)
- `imageio>=2.31.0` (current stable)
- All dependencies updated to compatible versions

## Troubleshooting Tips

1. **Always use a fresh conda environment** - don't try to install into an existing environment with conflicts
2. **Don't install xformers** unless you know you need it
3. **Use Python 3.12** for the most modern experience
4. **If something breaks**, start fresh with a clean environment
