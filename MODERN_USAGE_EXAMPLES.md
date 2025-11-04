# PyTTI Modern Usage Examples

This document shows how to use PyTTI's modernized features while preserving its unique aesthetic.

## What Makes PyTTI Special

PyTTI isn't just another img2img tool - it's an **iterative CLIP-guided optimization** system that creates unique, evolving visual effects. The key differences:

1. **Iterative Refinement**: PyTTI optimizes latent space over many steps, guided by CLIP embeddings
2. **Temporal Coherence**: Built-in optical flow and depth-based stabilization for smooth video
3. **3D Camera Movements**: Real depth-aware perspective transformations
4. **Rotoscoping**: Frame-accurate masking for compositing effects

Now with modern AI backends (Stable Diffusion, SAM 2, Depth-Anything-V2) - but keeping that PyTTI flavor!

---

## Installation

```bash
# Clone the repo
git clone --recurse-submodules https://github.com/pytti-tools/pytti-core
cd pytti-core

# Install modern dependencies
pip install -r requirements-modern.txt

# Install PyTTI
pip install -e .

# Optional: Install SAM 2 for AI rotoscoping
pip install git+https://github.com/facebookresearch/segment-anything-2.git
```

---

## Example 1: Basic Text-to-Video with Stable Diffusion XL

```python
from pytti import PyTTI

# Initialize with SDXL
pytti = PyTTI(
    image_model="Stable Diffusion XL",
    width=1024,
    height=1024,
)

# Generate with PyTTI's iterative optimization
video = pytti.generate_video(
    prompt="a serene mountain landscape at golden hour, oil painting style",
    animation_mode="2D",
    translate_x="t * 2",  # Slow pan
    steps_per_scene=200,  # More steps = more refinement (PyTTI style)
    duration=10.0,
    fps=12,
)

video.save("output.mp4")
```

**What's happening**: Unlike standard SD which generates once, PyTTI optimizes the latent space over 200 steps with CLIP guidance. This creates that characteristic "evolving" PyTTI aesthetic.

---

## Example 2: 3D Camera Movement with Modern Depth

```python
from pytti.image_models.diffusion import StableDiffusionImage
from pytti.depth_models import init_depth_model
from pytti.Transforms_modern import zoom_3d

# Initialize modern depth model
init_depth_model(model_type="depth_anything_v2", model_size="large")

# Create image model
img = StableDiffusionImage(
    width=1024,
    height=1024,
    model_id="sdxl",
)

# Initialize from prompt or image
img.encode_random()  # Or img.encode_image(pil_image)

# Apply PyTTI's signature 3D movement
# This uses depth to create parallax effect
flow, transformed = zoom_3d(
    img,
    translate=(0, 0, "t * 10"),  # Move forward through scene
    rotate=[1, 0, 0, 0],  # Quaternion rotation
    fov=60,
    depth_model_type="depth_anything_v2",  # Modern depth!
)
```

**What's special**: PyTTI's `zoom_3d` creates real 3D parallax by:
1. Estimating depth (now with Depth-Anything-V2)
2. Creating 3D point cloud from image + depth
3. Applying camera transformation matrices (PyGLM)
4. Reprojecting with perspective

The parametric motion (`t * 10`) adapts to scene depth statistics!

---

## Example 3: AI-Powered Rotoscoping with SAM 2

```python
from pytti.rotoscoper_v2 import AIRotoscoper

# Load video and segment automatically
rotoscoper = AIRotoscoper(
    "input_video.mp4",
    model_size="base",
)

# Method 1: Point-based segmentation (interactive)
rotoscoper.segment_with_points(
    frame_idx=0,
    points=[
        (512, 384, 1),  # x, y, label (1=foreground)
        (600, 400, 1),
        (100, 100, 0),  # 0=background
    ],
    auto_propagate=True,  # SAM 2 tracks through all frames!
)

# Method 2: Box-based segmentation
rotoscoper.segment_with_box(
    frame_idx=0,
    box=(100, 100, 500, 500),  # x1, y1, x2, y2
    auto_propagate=True,
)

# Save masks for verification
rotoscoper.save_masks("masks/")

# Apply to PyTTI generation
# The rotoscoper automatically registers with PyTTI's orchestrator
# Now run your PyTTI generation and masks will be applied!
```

**What's special**: SAM 2 automatically tracks the object through ALL frames. No more manual frame-by-frame masking!

---

## Example 4: Full Rotoscoping Workflow

```python
from pytti.rotoscoper_v2 import AIRotoscoper
from pytti.image_models.diffusion import StableDiffusionImage
from pytti.Perceptor.Embedder import HDMultiClipEmbedder
from pytti.ImageGuide import DirectImageGuide

# Step 1: AI Rotoscoping
rotoscoper = AIRotoscoper("person_walking.mp4", model_size="base")
rotoscoper.segment_with_points(
    frame_idx=0,
    points=[(640, 480, 1), (700, 500, 1)],  # Click on person
)

# Step 2: Set up image model
img = StableDiffusionImage(
    width=1024,
    height=1024,
    model_id="sdxl",
)

# Step 3: CLIP embedder (PyTTI's core)
embedder = HDMultiClipEmbedder(
    cutn=40,
    cut_pow=2,
)

# Step 4: Parse prompts
from pytti.Perceptor.Prompt import parse_prompt

prompts = [
    parse_prompt(embedder, "cyberpunk character, neon lights, futuristic:1.0"),
    parse_prompt(embedder, "detailed face, 8k, high quality:0.8"),
]

# Step 5: Create image guide and optimize
guide = DirectImageGuide(
    image_rep=img,
    embedder=embedder,
    lr=0.1,
)

# Step 6: Apply rotoscoping mask to target
rotoscoper.apply_to_target(img)

# Step 7: Run optimization loop
for frame_n in range(num_frames):
    # Update mask for current frame
    rotoscoper.update(frame_n)

    # Run PyTTI optimization steps
    for step in range(steps_per_frame):
        guide.run_steps(1, prompts, loss_augs=[])

    # Save frame
    img.decode_image().save(f"output/frame_{frame_n:04d}.png")
```

---

## Example 5: Config-Based Workflow (Hydra)

Create a config file: `configs/my_generation.yaml`

```yaml
# Modern PyTTI config
image_model: "Stable Diffusion XL"
diffusion_model_id: "sdxl"
width: 1024
height: 1024

# Modern depth for 3D
depth_model: "depth_anything_v2"
depth_model_size: "base"

# Animation
animation_mode: "3D"
translate_z_3d: "t * 5"  # Move forward
rotate_3d: "[1, 0, 0, 0]"

# Prompts
scenes: "a mystical forest, ethereal lighting, magical atmosphere:1.0"
scene_prefix: ""
scene_suffix: ""

# Optimization (PyTTI flavor)
steps_per_scene: 200
steps_per_frame: 50
learning_rate: 0.1

# CLIP guidance
cutouts: 40
cut_pow: 2

# Output
file_namespace: "mystical_forest"
save_every: 1
frames_per_second: 12

# Performance
use_fp16: true
enable_xformers: true
```

Run it:

```bash
python -m pytti.workhorse --config-name my_generation
```

---

## Example 6: Comparing Depth Models

```python
from pytti.depth_models import DepthAnythingV2, MarigoldDepth
from PIL import Image

image = Image.open("test_image.jpg")

# Fast and accurate (recommended)
depth_v2 = DepthAnythingV2(model_size="base")
depth_map_v2, _ = depth_v2.estimate_depth(image)

# Highest quality but slower
marigold = MarigoldDepth()
depth_map_marigold, _ = marigold.estimate_depth(image)

# Visualize depth maps
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
axes[0].imshow(image)
axes[0].set_title("Original")
axes[1].imshow(depth_map_v2, cmap='magma')
axes[1].set_title("Depth Anything V2")
axes[2].imshow(depth_map_marigold, cmap='magma')
axes[2].set_title("Marigold")
plt.show()
```

---

## Example 7: Model Switching

```python
from pytti.model_loader import get_model_loader, list_available_models, ModelType

# See all available models
diffusion_models = list_available_models(ModelType.DIFFUSION)
print("Available diffusion models:", diffusion_models.keys())

depth_models = list_available_models(ModelType.DEPTH)
print("Available depth models:", depth_models.keys())

# Load specific model
loader = get_model_loader()

# Try different diffusion models
sdxl = loader.load_diffusion_model("sdxl")
flux = loader.load_diffusion_model("flux_schnell")

# Switch between them
img_sdxl = StableDiffusionImage(1024, 1024, model_id="sdxl")
img_flux = FluxImage(1024, 1024, model_id="flux_schnell")

# Unload when done to free memory
loader.unload_model("sdxl")
```

---

## Example 8: Preset Configurations

```python
# Use built-in presets

# High-quality 3D animation
python -m pytti.workhorse preset=high_quality_3d \
    scenes="floating islands in the sky" \
    translate_z_3d="t * 10"

# AI rotoscoping
python -m pytti.workhorse preset=ai_rotoscope \
    video_path="input.mp4" \
    scenes="anime character"

# Fast Flux generation
python -m pytti.workhorse preset=flux \
    scenes="cyberpunk cityscape"

# SDXL generation
python -m pytti.workhorse preset=sdxl \
    scenes="surreal landscape"
```

---

## Example 9: Parametric Motion (PyTTI's Secret Sauce)

PyTTI's motion can adapt to scene depth using `r`, `R`, and `mu` variables:

```python
# r = minimum depth in scene
# R = maximum depth in scene
# mu = mean depth in scene

# Move faster in close scenes, slower in distant scenes
translate_z_3d = "r / 10"  # Adapts to nearest object

# Rotate based on depth range
rotate_3d = f"[cos(t), 0, sin(t) * (R - r) / R, 0]"

# Complex parametric motion
motion = "sin(t) * mu + cos(t * 2) * (R - r)"
```

This is what makes PyTTI's 3D feel more "intelligent" than simple linear motion!

---

## Example 10: Legacy Compatibility

Old PyTTI configs still work:

```python
# Old style (VQGAN)
python -m pytti.workhorse \
    image_model="VQGAN" \
    vqgan_model="wikiart" \
    scenes="abstract art" \
    animation_mode="3D"

# Modern style (same result, better quality)
python -m pytti.workhorse \
    image_model="Stable Diffusion XL" \
    scenes="abstract art" \
    animation_mode="3D" \
    depth_model="depth_anything_v2"
```

---

## Performance Tips

### Memory Optimization

```python
# Enable memory-efficient attention
img = StableDiffusionImage(
    width=1024,
    height=1024,
    model_id="sdxl",
    variant="fp16",  # Use half precision
)

# Enable xformers (if installed)
pipe.enable_xformers_memory_efficient_attention()

# Enable model CPU offload for very large models
pipe.enable_model_cpu_offload()
```

### Speed Optimization

```python
# Use smaller models
depth_model = "depth_anything_v2"
depth_model_size = "small"  # vs "base" or "large"

segmentation_model = "sam2_tiny"  # vs "base" or "large"

# Use turbo models
diffusion_model_id = "sdxl_turbo"  # Much faster than regular SDXL

# Use Flux Schnell (fast Flux variant)
image_model = "Flux Schnell"
```

### Quality Optimization

```python
# Use larger models
depth_model = "marigold"  # or "depth_anything_v2" with size="large"
segmentation_model = "sam2_large"

# More optimization steps (PyTTI's core)
steps_per_scene = 500
steps_per_frame = 200

# More cutouts for CLIP guidance
cutouts = 80
```

---

## Migration from Old PyTTI

### Old Code
```python
from pytti.image_models.vqgan import VQGANImage
from pytti.LossAug.DepthLossClass import DepthLoss, init_AdaBins

init_AdaBins()
img = VQGANImage(width, height, model="wikiart")
```

### New Code
```python
from pytti.image_models.diffusion import StableDiffusionImage
from pytti.depth_models import init_depth_model
from pytti.LossAug.DepthLossClass_modern import ModernDepthLoss

init_depth_model(model_type="depth_anything_v2")
img = StableDiffusionImage(width, height, model_id="sdxl")
```

### Configuration Migration
```yaml
# Old
image_model: "VQGAN"
vqgan_model: "wikiart"

# New (recommended)
image_model: "Stable Diffusion XL"
diffusion_model_id: "sdxl"

# Or keep old for compatibility
image_model: "VQGAN"  # Still works!
```

---

## What Stays the Same (PyTTI Flavor)

These are PyTTI's unique features that are PRESERVED:

✅ **Iterative CLIP-guided optimization** - Still the core of PyTTI
✅ **EMA (Exponential Moving Average)** - Smooth optimization
✅ **Parametric motion evaluation** - Motion adapts to scene depth
✅ **3D perspective transformations** - Real depth-aware camera math
✅ **Optical flow stabilization** - Temporal coherence for video
✅ **Rotoscoping orchestrator** - Multi-layer masking system
✅ **Loss orchestration** - Flexible multi-loss optimization
✅ **Scene interpolation** - Smooth prompt transitions

---

## What's New (Modern AI)

These are the MODERNIZED backends:

✨ **Stable Diffusion / Flux** - Modern image generation (vs VQGAN 2021)
✨ **Depth-Anything-V2** - State-of-the-art depth (vs AdaBins 2021)
✨ **SAM 2** - AI auto-segmentation (vs manual masks)
✨ **Modern CLIP variants** - SigLIP, EVA-CLIP (vs OpenAI CLIP 2021)
✨ **Better optical flow** - CoTracker, RAFT (vs GMA 2021)
✨ **ComfyUI-inspired architecture** - Clean model management
✨ **Modern dependencies** - PyTorch 2.5+, transformers 4.45+

---

## Troubleshooting

### "Model not found"
```python
# List available models
from pytti.model_loader import list_available_models
print(list_available_models())
```

### "Out of memory"
```python
# Use smaller sizes or fp16
img = StableDiffusionImage(
    width=512,  # Smaller
    height=512,
    variant="fp16",  # Half precision
)

# Or use gradient checkpointing
use_fp16 = True
```

### "SAM 2 not available"
```bash
pip install git+https://github.com/facebookresearch/segment-anything-2.git
```

### "Depth estimation slow"
```python
# Use smaller model
depth_model = "depth_anything_v2"
depth_model_size = "small"  # Much faster
```

---

## Next Steps

1. **Read the full plan**: `MODERNIZATION_PLAN.md`
2. **Check examples**: This file
3. **Try presets**: Start with `preset=sdxl` or `preset=high_quality_3d`
4. **Experiment**: PyTTI's magic comes from tweaking parameters!

**Remember**: PyTTI isn't about instant generation - it's about iterative refinement and evolution. Give it steps to work with (200+) and watch the magic happen!
