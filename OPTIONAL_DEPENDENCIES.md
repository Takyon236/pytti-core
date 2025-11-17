# Optional Dependencies Guide

## Core vs Optional Dependencies

pytti-core has two types of dependencies:

### Core Dependencies (Required)
These are automatically installed with `pip install -r requirements.txt`:
- PyTorch, torchvision
- TensorFlow
- Transformers
- CLIP
- Hydra, OmegaConf
- Pillow, imageio
- And others listed in requirements.txt

### Optional Dependencies (Advanced Features)
These provide extra features but are NOT required for basic operation:

#### 1. **pyttitools-gma** (Optical Flow / Motion Analysis)
- Enables advanced motion tracking and optical flow features
- Used by `OpticalFlowLoss` and related features
- Install: `pip install pyttitools-gma`
- If not installed: Motion analysis features will be disabled with a warning

#### 2. **pyttitools-adabins** (Depth Estimation)
- Enables depth estimation from images
- Used by `DepthLoss` and 3D features
- Install: `pip install pyttitools-adabins`
- If not installed: Depth estimation features will be disabled with a warning

#### 3. **xformers** (Memory Optimization)
- Optional memory optimization for transformers
- Can reduce VRAM usage
- Install: `pip install xformers>=0.0.22`
- **Warning:** Can be unstable, only install if you need it
- If not installed: Software works normally, just uses more VRAM

## Installation Options

### Minimal Installation (Recommended for most users)
```bash
pip install -r requirements.txt
pip install -e .
```

This installs all core dependencies. The software will run fine without optional dependencies.

### Full Installation (All Features)
```bash
pip install -r requirements.txt
pip install pyttitools-gma pyttitools-adabins
pip install -e .
```

This installs all optional dependencies for full functionality.

### Custom Installation
Pick only the features you need:

```bash
# Basic installation
pip install -r requirements.txt
pip install -e .

# Add optical flow only
pip install pyttitools-gma

# Add depth estimation only
pip install pyttitools-adabins

# Add memory optimization (careful - can break things)
pip install xformers
```

## What Happens Without Optional Dependencies?

### Without pyttitools-gma:
- ✅ Basic image generation works
- ✅ CLIP guidance works
- ✅ Most features work
- ❌ Optical flow stabilization disabled
- ❌ Motion analysis disabled
- You'll see: `GMA (Generalized Motion Aggregation) not available. Optical flow features will be disabled.`

### Without pyttitools-adabins:
- ✅ Basic image generation works
- ✅ CLIP guidance works
- ✅ Most features work
- ❌ Depth-based effects disabled
- ❌ 3D depth estimation disabled
- You'll see: `AdaBins not available. Depth estimation features will be disabled.`

### Without xformers:
- ✅ Everything works normally
- ⚠️ May use more VRAM
- No warning shown (it's truly optional)

## Troubleshooting

### "ModuleNotFoundError: No module named 'gma'"
**Solution:** This is expected if you haven't installed pyttitools-gma. Either:
1. Install it: `pip install pyttitools-gma`
2. Or ignore it - the software will work without optical flow features

### "ModuleNotFoundError: No module named 'adabins'"
**Solution:** This is expected if you haven't installed pyttitools-adabins. Either:
1. Install it: `pip install pyttitools-adabins`
2. Or ignore it - the software will work without depth features

### "Can't find pyttitools-gma or pyttitools-adabins on PyPI"
**Solution:** These packages may not be on PyPI or may have different names. Check:
1. GitHub repos: Look for official repos
2. Alternative names: May be `gma` and `adabins` directly
3. Or just run without them - they're optional

## Recommended Setup for Different Use Cases

### For Beginners / Basic Use:
```bash
pip install -r requirements.txt
pip install -e .
```
**Features:** All core image generation, CLIP guidance, basic animations

### For Video/Animation Work:
```bash
pip install -r requirements.txt
pip install pyttitools-gma  # For optical flow
pip install -e .
```
**Features:** + Motion tracking, flow stabilization

### For 3D/Depth Work:
```bash
pip install -r requirements.txt
pip install pyttitools-adabins  # For depth estimation
pip install -e .
```
**Features:** + Depth effects, 3D transformations

### For Power Users (Everything):
```bash
pip install -r requirements.txt
pip install pyttitools-gma pyttitools-adabins
# pip install xformers  # Only if you have VRAM issues
pip install -e .
```
**Features:** Everything enabled

## Current Status Check

To see what optional dependencies you have installed:

```bash
python -c "
try:
    import gma
    print('✓ GMA (optical flow) installed')
except:
    print('✗ GMA not installed (optical flow disabled)')

try:
    import adabins
    print('✓ AdaBins (depth estimation) installed')
except:
    print('✗ AdaBins not installed (depth disabled)')

try:
    import xformers
    print('✓ xformers (memory optimization) installed')
except:
    print('✗ xformers not installed (using normal memory mode)')
"
```
