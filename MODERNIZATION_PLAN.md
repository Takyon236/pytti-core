# PyTTI-Core Modernization Plan
## AI-Powered Video Generation & Rotoscoping Framework

**Date:** November 4, 2025
**Repository:** pytti-core
**Status:** Analysis Complete - Implementation Planning

---

## Executive Summary

PyTTI-Core is a sophisticated AI-powered video generation framework with unique strengths in **rotoscoping** and **3D effects**. The codebase uses CLIP-guided image generation with advanced temporal coherence techniques. However, the technology stack is significantly outdated (2021-2023 era). This plan outlines a comprehensive modernization strategy that preserves the core innovative techniques while updating to state-of-the-art AI image generation capabilities.

---

## 1. Current State Analysis

### 1.1 Core Technologies (Outdated)

| Component | Current Version | Latest Version | Gap |
|-----------|----------------|----------------|-----|
| PyTorch | 1.13.1 | 2.5+ | 2 major versions |
| TensorFlow | 2.7 | 2.18+ | Multiple versions |
| Transformers | 4.15.0 | 4.45+ | 30+ versions |
| CLIP | OpenAI Original | Multiple modern variants | Era: 2021 |
| VQGAN | Taming-Transformers | Newer alternatives | Era: 2021 |
| AdaBins | 2021 | Modern depth models | 4+ years |
| GMA (Optical Flow) | 2021 | Modern flow models | 4+ years |
| Kornia | 0.6.2 | 0.7.3+ | Major version |
| Pillow | 7.1 | 10.4+ | 3 major versions |
| ImageIO | 2.4.1 | 2.35+ | Major updates |

### 1.2 Core Strengths (To Preserve)

#### A. Rotoscoping System
- **Location:** `src/pytti/rotoscoper.py`
- **Functionality:** Frame-by-frame video masking with inversion support
- **Innovation:** Orchestrator pattern for multiple rotoscope layers
- **Key Features:**
  - Video frame extraction and processing
  - Mask application to image targets
  - Global rotoscope orchestrator for complex compositions

#### B. 3D Effects Engine
- **Location:** `src/pytti/Transforms.py`
- **Functionality:** Depth-based 3D transformations and camera movements
- **Key Components:**
  1. **Depth Estimation** (DepthLossClass.py):
     - AdaBins-based monocular depth estimation
     - Depth map generation for 3D reprojection

  2. **3D Transformations** (`zoom_3d`, `render_image_3d`):
     - Perspective matrix transformations using PyGLM
     - Camera movements (translate X/Y/Z, rotate, FOV)
     - Depth-aware image warping
     - Parametric motion (using depth statistics: r, R, mu)

  3. **2D Transformations** (`zoom_2d`, `animate_2d`):
     - Traditional affine transformations
     - Translation, rotation, zoom

#### C. Optical Flow System
- **Location:** `src/pytti/LossAug/OpticalFlowLossClass.py`
- **Functionality:** Video temporal coherence and stabilization
- **Key Components:**
  1. **Flow Estimation:** GMA-based forward/backward flow
  2. **Motion Edge Detection:** Consistency checking
  3. **Flow-based Warping:** Frame-to-frame coherence
  4. **Multi-scale Flow:** Long-term temporal samples

#### D. Animation Modes
1. **2D Animation:** Affine transformations (translate, rotate, zoom)
2. **3D Animation:** Depth-based camera movements
3. **Video Source:** Rotoscoping with optical flow stabilization

#### E. CLIP-Guided Generation
- **Location:** `src/pytti/Perceptor/`
- **Functionality:** Multi-CLIP model embeddings
- **Features:**
  - Multiple CLIP variants (ViT-B/32, ViT-B/16, ViT-L/14, ResNet variants)
  - Cutout-based optimization
  - Scene interpolation with prompt scheduling

#### F. Image Model Variety
1. **VQGAN:** Latent space optimization with vector quantization
2. **Pixel Image:** Limited palette with color quantization
3. **RGB Image:** Direct pixel optimization

### 1.3 Architecture Patterns (Good)

- ✅ **Hydra Configuration System:** Modern config management
- ✅ **Loss Orchestration:** Modular loss combination
- ✅ **Plugin Architecture:** Hydra plugins for extensibility
- ✅ **Differentiable Image Abstraction:** Clean model interface
- ✅ **EMA (Exponential Moving Average):** Stable optimization

### 1.4 Technical Debt

1. **Global State:** Excessive use of globals (VQGAN_MODEL, CLIP_PERCEPTORS, infer_helper)
2. **Subprocess Calls:** Unnecessary ffmpeg subprocess usage instead of OpenCV
3. **Mixed Concerns:** Rendering logic in workhorse.py needs refactoring
4. **Deprecated Patterns:** Static methods where instance methods would be cleaner
5. **Type Hints:** Minimal type annotations throughout codebase

---

## 2. Modernization Strategy

### Phase 1: Foundation Upgrade (Weeks 1-3)

#### 2.1 Dependency Updates
```yaml
Priority: CRITICAL
Risk: Medium
```

**Action Items:**
1. **PyTorch Ecosystem:**
   ```python
   torch >= 2.5.0
   torchvision >= 0.20.0
   pytorch-lightning >= 2.4.0
   kornia >= 0.7.3
   ```

2. **AI/ML Libraries:**
   ```python
   transformers >= 4.45.0
   diffusers >= 0.31.0  # NEW: Hugging Face diffusion models
   accelerate >= 0.34.0  # NEW: Multi-GPU optimization
   ```

3. **Computer Vision:**
   ```python
   Pillow >= 10.4.0
   imageio >= 2.35.0
   opencv-python >= 4.10.0
   ```

4. **Remove TensorFlow:** No longer needed with modern PyTorch

**Testing Strategy:**
- Create virtual environment for gradual migration
- Run existing test suite (`pytest --ignore=vendor -v -s`)
- Document breaking changes
- Create compatibility shims where necessary

#### 2.2 Code Quality Improvements
```yaml
Priority: HIGH
Risk: Low
```

**Action Items:**
1. **Type Annotations:**
   - Add type hints using `typing` module
   - Use `mypy` for static type checking
   - Target Python 3.10+ features

2. **Refactor Global State:**
   - Convert global variables to singleton classes
   - Use dependency injection patterns
   - Create model registry system

3. **Modern Python Patterns:**
   - Replace custom decorators with `functools` where applicable
   - Use dataclasses for configuration (already using `attrs`)
   - Add context managers for resource management

---

### Phase 2: AI Model Modernization (Weeks 4-8)

#### 2.3 Image Generation Backbone

**Current:** VQGAN + CLIP (2021)
**Modern Alternative:** Multi-model support with modern architectures

##### Option A: Stable Diffusion Integration
```yaml
Model: Stable Diffusion XL / SD3.5
Advantages:
  - State-of-the-art image quality
  - Large community and ecosystem
  - Extensive fine-tuning options
  - ControlNet support for conditioning
Implementation:
  - Use diffusers library
  - Add ControlNet for depth/edge/pose conditioning
  - Maintain latent space optimization path
```

**Integration Plan:**
```python
# New file: src/pytti/image_models/diffusion.py

class StableDiffusionImage(DifferentiableImage):
    """
    Stable Diffusion-based image representation.
    Supports various SD models: SD1.5, SDXL, SD3.5
    """

    def __init__(
        self,
        width: int,
        height: int,
        model_name: str = "stabilityai/stable-diffusion-xl-base-1.0",
        scale: int = 1,
        device: torch.device = None,
    ):
        # Initialize diffusion pipeline
        # Support ControlNet conditioning
        # Enable latent space optimization
        pass

    def encode_image(self, pil_image: Image.Image):
        # VAE encode to latent space
        pass

    def decode(self, latents: torch.Tensor):
        # VAE decode from latent space
        pass
```

##### Option B: Flux.1 Integration
```yaml
Model: Flux.1 (Black Forest Labs)
Advantages:
  - Cutting-edge quality (2024)
  - Superior text understanding
  - Fast inference
  - Open source variants available
Implementation:
  - Use diffusers library
  - Adapter for Flux architecture
  - Custom latent optimization
```

##### Option C: Hybrid Approach (RECOMMENDED)
```yaml
Strategy: Keep existing + add modern models
Advantages:
  - Backward compatibility
  - User choice
  - Gradual migration path
Models:
  - VQGAN (legacy, keep for compatibility)
  - Stable Diffusion XL
  - Flux.1
  - Future: Hunyuan-DiT, DALL-E integration
```

**Implementation:**
```python
# Update: src/pytti/config/structured_config.py

IMAGE_MODELS = [
    "Limited Palette",      # Legacy pixel-based
    "Unlimited Palette",    # Legacy RGB
    "VQGAN",               # Legacy VQGAN
    "Stable Diffusion XL", # NEW
    "Stable Diffusion 3.5", # NEW
    "Flux.1",              # NEW
]
```

#### 2.4 Depth Estimation Modernization

**Current:** AdaBins (2021)
**Modern Alternatives:**

##### Option 1: Depth Anything V2 (RECOMMENDED)
```yaml
Model: Depth-Anything-V2
Year: 2024
Advantages:
  - State-of-the-art accuracy
  - Fast inference
  - Multiple model sizes (small/base/large)
  - Better generalization
Source: https://github.com/DepthAnything/Depth-Anything-V2
```

##### Option 2: Marigold
```yaml
Model: Marigold (Diffusion-based depth)
Year: 2024
Advantages:
  - Diffusion-based (high quality)
  - Excellent detail preservation
  - Good for artistic applications
Trade-offs:
  - Slower inference
```

##### Option 3: ZoeDepth
```yaml
Model: ZoeDepth
Year: 2023
Advantages:
  - Metric depth estimation
  - Multiple domains (indoor/outdoor)
  - Good balance of speed/quality
```

**Implementation:**
```python
# New file: src/pytti/depth_models/__init__.py
# Refactor: src/pytti/LossAug/DepthLossClass.py

class ModernDepthEstimator:
    """Unified interface for depth estimation models"""

    MODELS = {
        'adabins': AdaBinsDepth,      # Legacy
        'depth_anything_v2': DepthAnythingV2,  # Recommended
        'marigold': MarigoldDepth,
        'zoedepth': ZoeDepth,
    }

    @staticmethod
    def create(model_name: str, device: torch.device):
        return ModernDepthEstimator.MODELS[model_name](device)
```

**Preserving 3D Techniques:**
- Keep existing `render_image_3d` function (Transforms.py:141-213)
- Keep PyGLM-based perspective transformations
- Keep parametric motion evaluation
- Update only the depth map source

#### 2.5 Optical Flow Modernization

**Current:** GMA (2021)
**Modern Alternatives:**

##### Option 1: RAFT (Updated) + Unimatch
```yaml
Model: RAFT / Unimatch
Year: 2023-2024
Advantages:
  - Better accuracy
  - Faster inference
  - Multi-frame support
```

##### Option 2: CoTracker
```yaml
Model: CoTracker (Meta)
Year: 2024
Advantages:
  - Point tracking
  - Long-term coherence
  - Video understanding
Use Case: Perfect for rotoscoping enhancement
```

##### Option 3: DIFT (Diffusion Features for Tracking)
```yaml
Model: DIFT
Year: 2024
Advantages:
  - Semantic correspondence
  - Works with diffusion models
  - No explicit optical flow
```

**Implementation (HYBRID APPROACH):**
```python
# New file: src/pytti/flow_models/__init__.py

class FlowEstimator:
    """Unified interface for optical flow estimation"""

    MODELS = {
        'gma': GMAFlow,           # Legacy
        'raft': RAFTFlow,         # Updated
        'unimatch': UnimatchFlow,
        'cotracker': CoTrackerFlow,  # For rotoscoping
    }

    def estimate_flow(
        self,
        frame1: torch.Tensor,
        frame2: torch.Tensor,
    ) -> torch.Tensor:
        # Unified flow estimation interface
        pass
```

**Preserving Optical Flow Techniques:**
- Keep `motion_edge_map` consistency checking (OpticalFlowLossClass.py:205-286)
- Keep flow-based warping (`apply_flow` in Transforms.py)
- Keep multi-scale temporal coherence
- Update only the flow estimation backend

#### 2.6 CLIP Modernization

**Current:** OpenAI CLIP (2021)
**Modern Alternatives:**

##### Multi-modal Encoders
```yaml
Models:
  - SigLIP (Google): Better than CLIP for many tasks
  - EVA-CLIP: Enhanced vision-language model
  - CLIP-L/14@336px: Higher resolution CLIP
  - OpenCLIP: Community models with various backbones
```

**Implementation:**
```python
# Update: src/pytti/Perceptor/Embedder.py

class ModernEmbedder(HDMultiClipEmbedder):
    """
    Enhanced embedder supporting modern vision-language models
    """

    SUPPORTED_MODELS = {
        # Legacy CLIP
        'ViT-B/32': 'openai/clip-vit-base-patch32',
        'ViT-L/14': 'openai/clip-vit-large-patch14',

        # Modern alternatives
        'SigLIP': 'google/siglip-so400m-patch14-384',
        'EVA-CLIP': 'BAAI/EVA-CLIP',
        'OpenCLIP-G': 'laion/CLIP-ViT-g-14-laion2B-s12B-b42K',
    }
```

---

### Phase 3: Enhanced Rotoscoping (Weeks 9-11)

#### 2.7 Advanced Rotoscoping Features

**Current:** Basic video frame masking
**Enhanced:** AI-powered segmentation and tracking

##### Integration 1: SAM 2 (Segment Anything Model 2)
```yaml
Model: SAM 2 (Meta)
Year: 2024
Features:
  - Video segmentation
  - Point/box/mask prompting
  - Temporal consistency
  - Real-time performance
Use Case: Automatic rotoscoping with minimal user input
```

**Implementation:**
```python
# New file: src/pytti/rotoscoper_v2.py

class AIRotoscoper:
    """
    AI-powered rotoscoping using SAM 2
    """

    def __init__(
        self,
        video_path: str,
        model_type: str = "sam2_large",
    ):
        self.sam2_model = load_sam2_model(model_type)
        self.video_frames = get_frames(video_path)
        self.masks = {}

    def segment_with_points(
        self,
        frame_idx: int,
        points: List[Tuple[int, int]],
        labels: List[int],
    ):
        """Interactive segmentation with point prompts"""
        # SAM 2 segmentation
        # Propagate to other frames
        pass

    def auto_track(self, initial_mask: np.ndarray):
        """Automatically track object through video"""
        # SAM 2 video tracking
        pass
```

##### Integration 2: CoTracker for Motion Tracking
```python
class MotionTracker:
    """
    Track points/regions through video for rotoscoping
    """

    def track_region(
        self,
        video: torch.Tensor,
        initial_mask: torch.Tensor,
    ) -> Dict[int, torch.Tensor]:
        """Track a masked region through all frames"""
        # CoTracker-based tracking
        # Returns mask for each frame
        pass
```

##### Integration 3: Mask Refinement
```python
class MaskRefiner:
    """
    Refine rotoscope masks using modern techniques
    """

    def temporal_smooth(self, masks: Dict[int, torch.Tensor]):
        """Smooth masks across time"""
        # Optical flow guided smoothing
        pass

    def edge_aware_refine(self, mask: torch.Tensor, image: Image.Image):
        """Refine mask edges using image gradients"""
        # Edge-aware refinement
        pass
```

#### 2.8 Enhanced Rotoscoping UI/API

**New Features:**
1. **Interactive Web UI** (optional):
   - Gradio-based interface
   - Point-and-click segmentation
   - Real-time preview

2. **Programmatic API:**
   ```python
   from pytti.rotoscoper_v2 import AIRotoscoper

   rotoscoper = AIRotoscoper("video.mp4")

   # Method 1: Interactive points
   rotoscoper.segment_with_points(
       frame_idx=0,
       points=[(100, 200), (150, 250)],
       labels=[1, 1]  # foreground
   )

   # Method 2: Auto-track from first frame
   rotoscoper.auto_track(initial_mask)

   # Method 3: Use with existing workflow
   scene = "a beautiful painting:1.0"
   rotoscoper.apply_to_prompt(scene, invert=False)
   ```

---

### Phase 4: Advanced 3D Effects (Weeks 12-14)

#### 2.9 Enhanced Depth-Based Effects

**Current:** Single depth map + basic 3D warping
**Enhanced:** Multi-depth techniques + advanced effects

##### Feature 1: Multi-frame Depth Consistency
```python
class ConsistentDepthEstimator:
    """
    Maintain temporal consistency in depth estimation
    """

    def estimate_video_depth(
        self,
        frames: List[Image.Image],
        model: str = "depth_anything_v2",
    ) -> List[np.ndarray]:
        """
        Estimate depth with temporal consistency
        """
        # Use optical flow to align depth maps
        # Temporal filtering
        # Return consistent depth sequence
        pass
```

##### Feature 2: Depth-Based Effects Library
```python
class DepthEffects:
    """
    Advanced depth-based visual effects
    """

    def depth_of_field(
        self,
        image: torch.Tensor,
        depth: torch.Tensor,
        focal_distance: float,
        aperture: float,
    ):
        """Simulate camera depth of field"""
        pass

    def atmospheric_perspective(
        self,
        image: torch.Tensor,
        depth: torch.Tensor,
        fog_color: Tuple[float, float, float],
        fog_density: float,
    ):
        """Add atmospheric haze based on depth"""
        pass

    def parallax_layers(
        self,
        image: torch.Tensor,
        depth: torch.Tensor,
        layers: int = 5,
    ):
        """Decompose image into parallax layers"""
        pass
```

##### Feature 3: 3D Camera Path Planning
```python
class CameraPathPlanner:
    """
    Advanced camera movement planning
    """

    def smooth_path(
        self,
        keyframes: List[CameraState],
        interpolation: str = "bezier",
    ):
        """Generate smooth camera path from keyframes"""
        pass

    def orbit_object(
        self,
        center: Tuple[float, float, float],
        radius: float,
        num_frames: int,
    ):
        """Create orbiting camera path"""
        pass
```

#### 2.10 NeRF-like 3D Reconstruction (Advanced)

**Optional Future Enhancement:**
```yaml
Feature: Novel view synthesis from video
Models:
  - Instant-NGP
  - Gaussian Splatting (3DGS)
  - DUSt3R (geometric understanding)
Use Case: Generate true 3D from rotoscoped video
Status: Future work (Phase 5)
```

---

### Phase 5: Performance & Scalability (Weeks 15-16)

#### 2.11 Optimization

##### GPU Acceleration
```python
# Use accelerate library for multi-GPU
from accelerate import Accelerator

accelerator = Accelerator()
model = accelerator.prepare(model)

# Automatic mixed precision
with torch.autocast('cuda'):
    output = model(input)
```

##### Compilation (PyTorch 2.0+)
```python
# Compile models for faster inference
model = torch.compile(model, mode='reduce-overhead')
```

##### Batching
```python
# Batch processing for video frames
def process_video_batch(frames: List[Image.Image], batch_size: int = 4):
    for i in range(0, len(frames), batch_size):
        batch = frames[i:i+batch_size]
        # Process batch in parallel
        yield process_batch(batch)
```

#### 2.12 Memory Management

```python
class MemoryEfficientPipeline:
    """
    Manage memory for large video processing
    """

    def __init__(self, max_vram_gb: float = 12.0):
        self.max_vram = max_vram_gb * 1024**3

    def process_with_checkpointing(self, video_path: str):
        """Process video with gradient checkpointing"""
        # Load frames on demand
        # Checkpoint intermediate results
        # Clear cache between steps
        pass
```

---

### Phase 6: API & User Experience (Weeks 17-18)

#### 2.13 Modern Python API

```python
# New file: src/pytti/api.py

from pytti import PyTTI

# Simple API
pytti = PyTTI(
    model="Stable Diffusion XL",
    depth_model="depth_anything_v2",
    flow_model="cotracker",
)

# Text-to-video with 3D motion
video = pytti.generate_video(
    prompt="a serene mountain landscape, golden hour",
    animation_mode="3D",
    camera_motion={
        "translate_z": "t * 5",  # Move forward
        "rotate_y": "sin(t) * 10",  # Gentle rotation
    },
    duration=10.0,  # seconds
    fps=30,
)

# Rotoscoping workflow
rotoscoped = pytti.rotoscope_video(
    input_video="input.mp4",
    prompt="transform into watercolor painting",
    auto_segment=True,  # AI segmentation
    preserve_motion=True,  # Optical flow
)

# Advanced: Multi-layer composition
composition = pytti.compose([
    {"video": "background.mp4", "prompt": "dreamy clouds", "layer": 0},
    {"video": "person.mp4", "prompt": "cyberpunk character", "layer": 1, "rotoscope": True},
    {"video": "foreground.mp4", "prompt": "rain particles", "layer": 2, "blend": "add"},
])
```

#### 2.14 CLI Modernization

```bash
# Current (Hydra-based)
python -m pytti.workhorse scenes="prompt" animation_mode=3D

# Enhanced
pytti generate \
  --prompt "a beautiful landscape" \
  --model sdxl \
  --animation 3D \
  --camera-motion "translate_z=t*5" \
  --output video.mp4

pytti rotoscope \
  --input video.mp4 \
  --prompt "anime style" \
  --segment-auto \
  --output rotoscoped.mp4
```

#### 2.15 Web UI (Optional)

```python
# New file: src/pytti/webui.py
import gradio as gr

def create_webui():
    with gr.Blocks() as demo:
        with gr.Tab("Generate"):
            prompt = gr.Textbox(label="Prompt")
            model = gr.Dropdown(choices=IMAGE_MODELS)
            generate_btn = gr.Button("Generate")

        with gr.Tab("Rotoscope"):
            video_input = gr.Video()
            segment_btn = gr.Button("Auto Segment")
            mask_editor = gr.Image(tool="sketch")

        with gr.Tab("3D Effects"):
            depth_model = gr.Dropdown(choices=DEPTH_MODELS)
            camera_controls = gr.Slider(label="Camera Z")

    return demo

if __name__ == "__main__":
    create_webui().launch()
```

---

## 3. Migration Roadmap

### Timeline Overview

```
Week 1-3:   Foundation (Dependencies, Code Quality)
Week 4-8:   AI Models (SD/Flux, Depth, Flow, CLIP)
Week 9-11:  Rotoscoping (SAM 2, CoTracker)
Week 12-14: 3D Effects (Enhanced depth, effects library)
Week 15-16: Performance (Optimization, memory)
Week 17-18: API/UX (Python API, CLI, Web UI)
```

### Parallel Development Strategy

```
Track 1 (Core):     Dependency updates → Model integration
Track 2 (Features): Rotoscoping → 3D effects
Track 3 (DevEx):    API design → Documentation
```

---

## 4. Backward Compatibility Strategy

### 4.1 Compatibility Layer

```python
# New file: src/pytti/compat.py

class LegacyVQGAN:
    """Wrapper for old VQGAN interface"""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "VQGANImage is deprecated. Use StableDiffusionImage instead.",
            DeprecationWarning
        )
        # Delegate to old implementation
```

### 4.2 Configuration Migration

```python
# Automatic config migration
def migrate_config_v1_to_v2(old_config: dict) -> dict:
    """Migrate old config format to new format"""

    new_config = old_config.copy()

    # Map old model names to new
    model_mapping = {
        "VQGAN": "VQGAN (legacy)",
        "Limited Palette": "Pixel (legacy)",
    }

    if old_config["image_model"] in model_mapping:
        new_config["image_model"] = model_mapping[old_config["image_model"]]

    return new_config
```

### 4.3 Deprecation Warnings

```python
@deprecated(version="2.0", alternative="StableDiffusionImage")
class VQGANImage:
    pass
```

---

## 5. Testing Strategy

### 5.1 Test Coverage

```yaml
Unit Tests:
  - Image models (VQGAN, SD, Flux)
  - Depth estimation (all models)
  - Optical flow (all models)
  - Rotoscoping (legacy + AI)
  - 3D transformations
  - Loss functions

Integration Tests:
  - End-to-end video generation
  - Rotoscoping workflow
  - 3D animation pipeline
  - Multi-model switching

Performance Tests:
  - Memory usage benchmarks
  - Speed benchmarks (FPS)
  - GPU utilization
  - Batch processing

Regression Tests:
  - Compare output with legacy version
  - Visual similarity metrics (LPIPS, SSIM)
  - Ensure core techniques preserved
```

### 5.2 Test Infrastructure

```python
# New file: tests/test_modernization.py

class TestModernization:

    def test_depth_comparison(self):
        """Compare AdaBins vs Depth-Anything-V2"""
        image = load_test_image()

        depth_adabins = estimate_depth_adabins(image)
        depth_v2 = estimate_depth_anything_v2(image)

        # Check shapes match
        assert depth_adabins.shape == depth_v2.shape

        # Check correlation (should be high)
        correlation = np.corrcoef(
            depth_adabins.flatten(),
            depth_v2.flatten()
        )[0, 1]
        assert correlation > 0.8

    def test_3d_transform_preserved(self):
        """Ensure 3D transforms work with new depth model"""
        # Test zoom_3d with new depth model
        # Verify output matches expected behavior
        pass
```

---

## 6. Documentation Plan

### 6.1 User Documentation

```
docs/
├── getting-started.md
├── migration-guide.md          # v1 → v2 migration
├── tutorials/
│   ├── text-to-video.md
│   ├── rotoscoping.md
│   ├── 3d-effects.md
│   └── advanced-composition.md
├── api-reference/
│   ├── models.md
│   ├── rotoscoper.md
│   ├── transforms.md
│   └── loss-functions.md
└── comparison.md               # Old vs New models
```

### 6.2 Developer Documentation

```
dev-docs/
├── architecture.md
├── adding-models.md
├── contributing.md
└── performance-tuning.md
```

---

## 7. Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking changes in dependencies | High | Medium | Version pinning, extensive testing |
| Performance regression | Medium | Low | Benchmarking, profiling |
| Quality degradation | High | Low | Visual comparison tests, user feedback |
| Memory issues with larger models | Medium | Medium | Gradient checkpointing, model quantization |
| User adoption resistance | Low | Medium | Clear migration guide, backward compatibility |
| License incompatibilities | Medium | Low | License audit of new models |

---

## 8. Success Metrics

### 8.1 Technical Metrics

- [ ] **Speed:** 2x faster video generation (via optimizations)
- [ ] **Quality:** Improved visual quality (human evaluation)
- [ ] **Memory:** Support 4K resolution (vs current ~1K limit)
- [ ] **Compatibility:** 100% test pass rate
- [ ] **Coverage:** 80%+ code coverage

### 8.2 User Metrics

- [ ] **Migration:** 90% of users successfully migrate
- [ ] **Adoption:** 50% of users try new models within 3 months
- [ ] **Satisfaction:** 4.5+/5 average rating (survey)
- [ ] **Performance:** <5% reported bugs in stable release

---

## 9. Key Preservation Requirements

### 9.1 Must Preserve (Core Innovation)

✅ **Rotoscoping System:**
- Frame-by-frame masking
- Inversion support
- Multi-layer orchestration

✅ **3D Effects:**
- `render_image_3d` function and algorithm
- PyGLM-based perspective transformations
- Parametric camera motion (r, R, mu)
- Depth-aware warping

✅ **Optical Flow:**
- `motion_edge_map` consistency checking
- Flow-based warping (`apply_flow`)
- Multi-scale temporal coherence

✅ **Animation Modes:**
- 2D, 3D, Video Source modes
- Scene interpolation
- Prompt scheduling

✅ **Configuration System:**
- Hydra-based config
- YAML configuration files
- CLI arguments

### 9.2 Can Modernize (Implementation Details)

✓ Depth estimation backend (AdaBins → Depth-Anything-V2)
✓ Optical flow backend (GMA → RAFT/CoTracker)
✓ Image generation (VQGAN → SD/Flux)
✓ CLIP variants (OpenAI → SigLIP/EVA-CLIP)
✓ Global state → Singleton/DI pattern
✓ Subprocess calls → Native Python/OpenCV

---

## 10. Recommended Implementation Order

### Priority 1 (Critical Path)
1. Dependency updates (PyTorch, transformers)
2. Stable Diffusion integration
3. Depth-Anything-V2 integration
4. Basic testing and validation

### Priority 2 (High Value)
5. SAM 2 rotoscoping
6. CoTracker optical flow
7. Enhanced 3D effects library
8. Performance optimization

### Priority 3 (Nice to Have)
9. Flux.1 integration
10. Web UI
11. Advanced effects
12. Comprehensive documentation

---

## 11. Next Steps

### Immediate Actions (This Week)

1. **Create Development Branch:**
   ```bash
   git checkout -b feature/modernization
   ```

2. **Set Up Test Environment:**
   ```bash
   conda create -n pytti-modern python=3.10
   conda activate pytti-modern
   ```

3. **Baseline Testing:**
   ```bash
   # Document current performance
   pytest --benchmark-only
   # Save sample outputs for comparison
   python -m pytti.workhorse --config tests/baseline_config.yaml
   ```

4. **Start Dependency Migration:**
   - Create `requirements-modern.txt`
   - Test PyTorch 2.5 compatibility
   - Document breaking changes

### Decision Points

**Question 1:** Which image generation model to prioritize?
- [ ] Option A: Stable Diffusion XL (most mature)
- [ ] Option B: Flux.1 (cutting edge)
- [ ] Option C: Both (recommended)

**Question 2:** Depth model selection?
- [ ] Option A: Depth-Anything-V2 (recommended)
- [ ] Option B: Marigold (higher quality, slower)
- [ ] Option C: Support multiple (best flexibility)

**Question 3:** Breaking changes acceptable?
- [ ] Yes, major version bump (v2.0)
- [ ] No, maintain v1.x compatibility

**Question 4:** Web UI priority?
- [ ] High (include in v2.0)
- [ ] Medium (v2.1 release)
- [ ] Low (community contribution)

---

## 12. Resources & References

### Model Resources

**Image Generation:**
- Stable Diffusion: https://github.com/Stability-AI/stablediffusion
- Flux.1: https://github.com/black-forest-labs/flux
- Diffusers: https://github.com/huggingface/diffusers

**Depth Estimation:**
- Depth-Anything-V2: https://github.com/DepthAnything/Depth-Anything-V2
- Marigold: https://github.com/prs-eth/marigold
- ZoeDepth: https://github.com/isl-org/ZoeDepth

**Segmentation & Tracking:**
- SAM 2: https://github.com/facebookresearch/segment-anything-2
- CoTracker: https://github.com/facebookresearch/co-tracker

**Optical Flow:**
- RAFT: https://github.com/princeton-vl/RAFT
- Unimatch: https://github.com/autonomousvision/unimatch

**Vision-Language Models:**
- SigLIP: https://huggingface.co/google/siglip-so400m-patch14-384
- EVA-CLIP: https://github.com/baaivision/EVA

### Learning Resources
- PyTorch 2.0 Tutorial: https://pytorch.org/tutorials/
- Diffusers Documentation: https://huggingface.co/docs/diffusers
- Hydra Tutorial: https://hydra.cc/docs/intro/

---

## Conclusion

This modernization plan provides a comprehensive roadmap to transform PyTTI-Core from a 2021-era CLIP+VQGAN system into a cutting-edge 2025 AI video generation framework while **preserving its unique strengths in rotoscoping and 3D effects**.

The hybrid approach ensures:
- ✅ Backward compatibility with existing workflows
- ✅ Gradual migration path for users
- ✅ Core innovation (rotoscoping, 3D) preserved
- ✅ Modern AI capabilities (SD/Flux, SAM 2, etc.)
- ✅ Improved performance and scalability
- ✅ Better developer and user experience

**Estimated Total Effort:** 18 weeks (4.5 months) with 1-2 developers
**Recommended Start Date:** As soon as stakeholders approve
**Target Release:** Q2 2026 (Beta), Q3 2026 (Stable)

---

**Document Version:** 1.0
**Author:** AI Software Development Expert
**Last Updated:** November 4, 2025
