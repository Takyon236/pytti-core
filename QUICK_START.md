# PyTTI Modern - Quick Start Guide

Get started with PyTTI in 5 minutes! This guide covers installation and your first generation.

---

## 📦 Installation

### 1. Basic Installation

```bash
# Clone the repository
git clone --recurse-submodules https://github.com/pytti-tools/pytti-core
cd pytti-core

# Install modern dependencies
pip install -r requirements-modern.txt

# Install PyTTI
pip install -e .
```

### 2. Validate Installation

```bash
# Run the validation script
python validate_installation.py

# Should show green ✓ for all core components
```

### 3. Optional: Install AI Rotoscoping

```bash
# For SAM 2 automatic video segmentation
pip install git+https://github.com/facebookresearch/segment-anything-2.git
```

---

## 🚀 Your First Generation

### Option 1: Use a Preset (Easiest)

```bash
# SDXL generation (recommended)
python -m pytti.workhorse \
  preset=sdxl_default \
  scenes="a mystical forest at golden hour, ethereal lighting"

# High-quality 3D animation
python -m pytti.workhorse \
  preset=high_quality_3d \
  scenes="floating islands in the sky" \
  translate_z_3d="t * 5"

# Fast testing
python -m pytti.workhorse \
  preset=fast_test \
  scenes="cyberpunk cityscape"
```

### Option 2: Create Custom Config

Create `my_config.yaml`:

```yaml
# Modern SDXL config
image_model: "Stable Diffusion XL"
width: 1024
height: 1024

# Scene description
scenes: "a serene mountain landscape"

# PyTTI's iterative optimization
steps_per_scene: 200
learning_rate: 0.1

# Output
file_namespace: "my_generation"
save_every: 50
```

Run it:

```bash
python -m pytti.workhorse --config-name my_config
```

### Option 3: Python API

```python
from pytti.image_models.diffusion import StableDiffusionImage
from pytti.Perceptor.Embedder import HDMultiClipEmbedder
from pytti.Perceptor.Prompt import parse_prompt

# Create SDXL image model
img = StableDiffusionImage(
    width=1024,
    height=1024,
    model_id="sdxl",
)

# Random initialization
img.encode_random()

# Create CLIP embedder
embedder = HDMultiClipEmbedder(cutn=40, cut_pow=2)

# Parse prompt
prompt = parse_prompt(embedder, "a mystical forest:1.0")

# Optimize! (PyTTI's magic - iterative refinement)
for step in range(200):
    # Your optimization loop here
    # See MODERN_USAGE_EXAMPLES.md for full example
    pass

# Save result
img.decode_image().save("output.png")
```

---

## 🎯 Available Presets

PyTTI comes with ready-to-use presets:

| Preset | Model | Speed | Quality | Use Case |
|--------|-------|-------|---------|----------|
| `sdxl_default` | SDXL | Medium | Excellent | General purpose (recommended) |
| `flux_fast` | Flux Schnell | Fast | Excellent | Quick high-quality |
| `high_quality_3d` | SDXL | Slow | Best | 3D animations |
| `ai_rotoscope` | SDXL | Medium | Excellent | Video + AI segmentation |
| `fast_test` | SDXL Turbo | Very Fast | Good | Testing prompts |

---

## 🎨 Examples by Use Case

### Static Image Generation

```bash
python -m pytti.workhorse \
  preset=sdxl_default \
  scenes="a beautiful sunset over mountains, oil painting style" \
  steps_per_scene=300
```

### 2D Animation (Pan/Zoom)

```bash
python -m pytti.workhorse \
  preset=sdxl_default \
  animation_mode=2D \
  translate_x="t * 2" \
  scenes="a mystical forest"
```

### 3D Animation (Camera Movement)

```bash
python -m pytti.workhorse \
  preset=high_quality_3d \
  animation_mode=3D \
  translate_z_3d="t * 10" \
  scenes="floating islands in the sky"
```

### Video Rotoscoping

```bash
python -m pytti.workhorse \
  preset=ai_rotoscope \
  video_path="input_video.mp4" \
  scenes="transform into anime style"
```

---

## 🔧 Common Adjustments

### Change Image Quality

```yaml
# Lower quality but faster
steps_per_scene: 100
width: 512
height: 512

# Higher quality but slower
steps_per_scene: 500
width: 1024
height: 1024
```

### Adjust CLIP Guidance

```yaml
# Stronger CLIP guidance (more stylized)
cutouts: 80
cut_pow: 3

# Weaker CLIP guidance (more realistic)
cutouts: 20
cut_pow: 1
```

### Control Learning Rate

```yaml
# Faster changes (less smooth)
learning_rate: 0.2

# Slower changes (more smooth)
learning_rate: 0.05
```

---

## ⚙️ Performance Tips

### Reduce VRAM Usage

```yaml
use_fp16: true          # Half precision (50% less VRAM)
width: 512              # Smaller dimensions
height: 512
cutouts: 20             # Fewer cutouts
```

### Increase Speed

```yaml
# Use faster models
image_model: "SDXL Turbo"
depth_model_size: "small"

# Fewer steps
steps_per_scene: 100
```

### Maximize Quality

```yaml
# Best models
depth_model_size: "large"

# More steps
steps_per_scene: 500
steps_per_frame: 200

# More cutouts
cutouts: 80
```

---

## 🐛 Troubleshooting

### "Out of Memory"

```bash
# Use smaller dimensions or fp16
python -m pytti.workhorse \
  preset=fast_test \
  width=512 \
  height=512 \
  use_fp16=true
```

### "Model Not Found"

```python
# List available models
from pytti.model_loader import list_available_models
print(list_available_models())
```

### "Slow Generation"

```bash
# Use turbo model for testing
python -m pytti.workhorse \
  preset=fast_test \
  scenes="your prompt"
```

### "Dependencies Missing"

```bash
# Re-run validation
python validate_installation.py --verbose

# Install missing deps
pip install -r requirements-modern.txt
```

---

## 📖 Next Steps

1. **Read Examples**: [MODERN_USAGE_EXAMPLES.md](MODERN_USAGE_EXAMPLES.md) - 10 detailed examples
2. **Explore Presets**: Try different presets to find your workflow
3. **Tweak Parameters**: Experiment with `steps_per_scene`, `learning_rate`, `cutouts`
4. **3D Effects**: Learn about depth-based camera movements
5. **AI Rotoscoping**: Try automatic video segmentation

---

## 💡 Key Concepts

### What Makes PyTTI Special

1. **Iterative Optimization**: Not one-shot generation, but gradual refinement over 200+ steps
2. **CLIP Guidance**: Uses CLIP embeddings to guide the optimization
3. **Temporal Coherence**: Built-in optical flow for smooth video
4. **3D Camera Math**: Real depth-aware perspective transformations
5. **Parametric Motion**: Camera moves that adapt to scene depth

### The PyTTI "Flavor"

PyTTI creates distinctive evolving visuals because:
- It optimizes over many steps (not instant)
- CLIP guidance creates unique aesthetic
- Temporal smoothing with EMA
- Depth-aware 3D effects

Give it time (200+ steps) and watch the magic happen!

---

## 🆘 Need Help?

- **Documentation**: [MODERNIZATION_README.md](MODERNIZATION_README.md)
- **Examples**: [MODERN_USAGE_EXAMPLES.md](MODERN_USAGE_EXAMPLES.md)
- **Full Plan**: [MODERNIZATION_PLAN.md](MODERNIZATION_PLAN.md)
- **Issues**: https://github.com/pytti-tools/pytti-core/issues
- **Validation**: `python validate_installation.py`
- **Config Migration**: `python migrate_config.py old_config.yaml`

---

**Ready to create?** Start with a preset and experiment! 🎨✨

```bash
python -m pytti.workhorse preset=sdxl_default scenes="your imagination here"
```
