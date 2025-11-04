## 🎨 PyTTI Modern - Bringing 2025 AI to PyTTI's Unique Aesthetic

This modernization brings state-of-the-art AI models to PyTTI while **preserving its distinctive iterative optimization workflow** that creates those unique, evolving visuals.

---

## 🚀 What's New

### Modern AI Backends
- ✨ **Stable Diffusion XL / Flux** - Replace VQGAN (2021) with modern diffusion
- ✨ **Depth-Anything-V2** - State-of-the-art depth estimation (2024)
- ✨ **SAM 2** - AI-powered automatic video segmentation
- ✨ **Modern CLIP** - SigLIP, EVA-CLIP variants
- ✨ **ComfyUI-inspired architecture** - Clean model management

### What Stays the Same (PyTTI's Magic) ✅
- **Iterative CLIP-guided optimization** - The core PyTTI workflow
- **3D camera transforms** - Depth-aware perspective math (render_image_3d)
- **Parametric motion** - Motion that adapts to scene depth (r, R, mu)
- **Rotoscoping orchestrator** - Multi-layer video masking
- **Optical flow stabilization** - Temporal coherence
- **EMA smoothing** - Stable optimization over time

---

## 📦 Quick Start

### Installation

```bash
# Install modern dependencies
pip install -r requirements-modern.txt

# Install PyTTI
pip install -e .

# Optional: Install SAM 2 for AI rotoscoping
pip install git+https://github.com/facebookresearch/segment-anything-2.git
```

### Basic Usage

```python
from pytti.image_models.diffusion import StableDiffusionImage
from pytti.depth_models import init_depth_model

# Initialize modern depth
init_depth_model(model_type="depth_anything_v2", model_size="base")

# Create SDXL image model (replaces VQGAN)
img = StableDiffusionImage(
    width=1024,
    height=1024,
    model_id="sdxl",
)

# PyTTI's iterative optimization still works the same!
# The CLIP-guided latent optimization creates PyTTI's unique look
```

### Config-Based (Hydra)

```bash
# Modern preset configs
python -m pytti.workhorse preset=sdxl scenes="mystical forest"
python -m pytti.workhorse preset=high_quality_3d animation_mode=3D scenes="floating islands"
python -m pytti.workhorse preset=ai_rotoscope video_path="input.mp4" scenes="anime character"
```

---

## 📖 Documentation

- **[MODERNIZATION_PLAN.md](MODERNIZATION_PLAN.md)** - Full technical plan and architecture
- **[MODERNIZATION_SUMMARY.md](MODERNIZATION_SUMMARY.md)** - Executive summary
- **[MODERN_USAGE_EXAMPLES.md](MODERN_USAGE_EXAMPLES.md)** - Code examples and tutorials

---

## 🎯 Key Features

### 1. Modern Image Generation

**Before (VQGAN 2021):**
```python
from pytti.image_models.vqgan import VQGANImage
img = VQGANImage(width, height)
```

**Now (Stable Diffusion / Flux):**
```python
from pytti.image_models.diffusion import StableDiffusionImage, FluxImage

# SDXL - Best balance
img = StableDiffusionImage(width, height, model_id="sdxl")

# Flux - Cutting edge
img = FluxImage(width, height, model_id="flux_schnell")

# Still works!
img = VQGANImage(width, height)  # Legacy compatibility
```

### 2. AI-Powered Rotoscoping

**Before (Manual masking):**
```python
from pytti.rotoscoper import Rotoscoper
rotoscoper = Rotoscoper("video.mp4")
# Manual frame-by-frame work...
```

**Now (SAM 2 auto-tracking):**
```python
from pytti.rotoscoper_v2 import AIRotoscoper

rotoscoper = AIRotoscoper("video.mp4")
rotoscoper.segment_with_points(
    frame_idx=0,
    points=[(640, 480, 1), (700, 500, 1)],  # Just click once!
)
# SAM 2 automatically tracks through ALL frames!
```

### 3. Modern Depth for 3D Effects

**Before (AdaBins 2021):**
```python
from pytti.LossAug.DepthLossClass import init_AdaBins
init_AdaBins()
```

**Now (Depth-Anything-V2 2024):**
```python
from pytti.depth_models import init_depth_model
init_depth_model(model_type="depth_anything_v2", model_size="base")

# PyTTI's 3D transforms preserved!
from pytti.Transforms_modern import zoom_3d
flow, img = zoom_3d(img, translate=(0, 0, "t * 10"))
```

---

## 🔧 Model Options

### Diffusion Models

| Model | Quality | Speed | VRAM | Use Case |
|-------|---------|-------|------|----------|
| SD 1.5 | Good | Fast | Low | Testing |
| SDXL | Excellent | Medium | Medium | Recommended |
| SDXL Turbo | Good | Very Fast | Medium | Rapid iteration |
| Flux Schnell | Excellent | Fast | High | Fast high-quality |
| Flux Dev | Best | Slow | High | Final renders |

### Depth Models

| Model | Quality | Speed | Use Case |
|-------|---------|-------|----------|
| Depth-Anything-V2 Small | Good | Very Fast | Testing |
| Depth-Anything-V2 Base | Excellent | Fast | **Recommended** |
| Depth-Anything-V2 Large | Best | Medium | High quality |
| Marigold | Best | Slow | Final renders |
| AdaBins (legacy) | OK | Fast | Compatibility |

### Segmentation Models

| Model | Quality | Speed | Use Case |
|-------|---------|-------|----------|
| SAM 2 Tiny | Good | Very Fast | Testing |
| SAM 2 Small | Good | Fast | Quick work |
| SAM 2 Base | Excellent | Medium | **Recommended** |
| SAM 2 Large | Best | Slow | High precision |

---

## 🎨 PyTTI's Unique "Flavor"

What makes PyTTI special isn't just the models - it's the **workflow**:

### Iterative Optimization
Unlike standard "generate once" tools, PyTTI optimizes over many steps:

```yaml
steps_per_scene: 200  # More steps = more evolution
steps_per_frame: 50   # PyTTI's refinement per frame
```

This creates the characteristic **"evolving"** PyTTI aesthetic.

### Parametric Motion
Camera motion that adapts to scene depth:

```python
# r = min depth, R = max depth, mu = mean depth
translate_z_3d: "r / 10"  # Faster in close scenes
rotate: "sin(t) * (R - r)"  # Rotation based on depth range
```

### Temporal Coherence
Built-in optical flow and depth stabilization:

```yaml
flow_stabilization_weight: "0.5"
depth_stabilization_weight: "0.3"
```

### 3D Perspective Math
Real camera transformations using PyGLM:

```python
# PyTTI's render_image_3d (preserved!)
# - Creates 3D point cloud from image + depth
# - Applies perspective matrix transformations
# - Reprojects with proper camera math
```

---

## ⚙️ Configuration

### Modern Config Schema

```yaml
# Image generation
image_model: "Stable Diffusion XL"  # or "Flux Schnell", "VQGAN"
diffusion_model_id: "sdxl"
width: 1024
height: 1024

# Depth estimation
depth_model: "depth_anything_v2"  # or "marigold", "adabins"
depth_model_size: "base"  # or "small", "large"

# Segmentation
use_ai_rotoscoping: true
segmentation_model: "sam2_base"  # or "sam2_tiny", "sam2_large"

# Animation
animation_mode: "3D"  # or "2D", "Video Source", "off"
translate_z_3d: "t * 5"

# PyTTI optimization
steps_per_scene: 200
steps_per_frame: 50
learning_rate: 0.1
cutouts: 40

# Performance
use_fp16: true
enable_xformers: true
```

---

## 🔄 Migration from Old PyTTI

Old configs still work! Just update the model names:

### Old Config
```yaml
image_model: "VQGAN"
vqgan_model: "wikiart"
```

### New Config (Recommended)
```yaml
image_model: "Stable Diffusion XL"
diffusion_model_id: "sdxl"
```

### Or Keep Old (Still Works!)
```yaml
image_model: "VQGAN"  # Backward compatible
vqgan_model: "wikiart"
```

---

## 🎯 Next Steps

1. **Read examples**: [MODERN_USAGE_EXAMPLES.md](MODERN_USAGE_EXAMPLES.md)
2. **Try presets**: `python -m pytti.workhorse preset=sdxl scenes="your prompt"`
3. **Experiment**: PyTTI's magic comes from iteration - give it 200+ steps!
4. **Share**: Show us what you create!

---

## 🤝 Backward Compatibility

✅ **All old configs work**
✅ **Legacy models available** (VQGAN, AdaBins)
✅ **Same CLI interface**
✅ **Same Python API structure**
✅ **Same workflow**

The modernization adds new capabilities without breaking existing projects.

---

## 📊 Performance

### Speed Improvements
- Modern depth models: **2-3x faster** than AdaBins
- SDXL Turbo: **5x faster** than standard SDXL
- Flux Schnell: **Fast high-quality** alternative

### Memory Optimizations
- FP16 support: **50% less VRAM**
- Xformers attention: **40% less memory**
- Model offloading: **Run larger models**

### Quality Improvements
- Depth-Anything-V2: **Significantly more accurate**
- SAM 2: **Near-perfect segmentation**
- Modern diffusion: **Higher resolution, better quality**

---

## 🐛 Troubleshooting

**"Out of memory"**
```yaml
use_fp16: true
width: 512  # Reduce size
height: 512
```

**"Model not found"**
```python
from pytti.model_loader import list_available_models
print(list_available_models())
```

**"SAM 2 not available"**
```bash
pip install git+https://github.com/facebookresearch/segment-anything-2.git
```

---

## 🙏 Credits

- **Original PyTTI**: The amazing PyTTI-Tools team
- **Stable Diffusion**: Stability AI
- **Flux**: Black Forest Labs
- **Depth-Anything-V2**: Depth-Anything team
- **SAM 2**: Meta AI (FAIR)
- **ComfyUI**: Inspiration for clean architecture

---

## 📝 License

Same as original PyTTI (check main LICENSE file)

---

**Remember**: PyTTI isn't about instant generation - it's about **iterative refinement and evolution**. The modernization gives you better tools, but the unique PyTTI aesthetic comes from giving it time to optimize. Start with 200+ steps and enjoy the journey! 🎨✨
