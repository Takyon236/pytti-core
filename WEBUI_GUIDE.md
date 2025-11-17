# PyTTI Modern - Web UI Guide

Welcome to PyTTI's Gradio-based web interface! This guide will help you get started with the browser-based UI for AI video generation.

---

## 🚀 Quick Start

### 1. Installation

First, make sure you have PyTTI core and modern dependencies installed:

```bash
# Install core PyTTI
pip install -r requirements.txt
pip install -r requirements-modern.txt

# Install Web UI dependencies
pip install -r requirements-webui.txt

# Install PyTTI in development mode
pip install -e .
```

### 2. Launch the Web UI

```bash
# Launch locally (opens browser automatically)
python -m pytti.webui

# Or use the app.py directly
python -m pytti.webui.app
```

The web UI will open at `http://localhost:7860`

### 3. Advanced Launch Options

```bash
# Create shareable link (for remote access)
python -m pytti.webui --share

# Custom port
python -m pytti.webui --port 8080

# Don't open browser automatically
python -m pytti.webui --no-browser

# Force CPU mode (no GPU)
python -m pytti.webui --cpu
```

---

## 🎨 Using the Web UI

### Main Interface Layout

The web UI is organized into two main columns:

**Left Column: Controls**
- Preset selector
- Model selection
- Prompt input
- Parameter controls (basic, CLIP, advanced)
- Generate/Stop buttons

**Right Column: Preview & Output**
- Live image preview
- Progress bar and step counter
- Generation info
- Download and save options

---

## 📋 Quick Workflow

### 1. Choose a Preset

Start by selecting a preset from the **Quick Presets** section:

- **SDXL Default (Recommended)** - Balanced quality and speed
- **Flux Fast** - Quick, high-quality results
- **High Quality 3D** - Best for 3D animations
- **Fast Test** - Quick testing mode
- **Custom** - Manual configuration

Presets automatically configure model, resolution, steps, and other parameters.

### 2. Enter Your Prompt

In the **Prompt** section, describe what you want to create:

```
Example prompts:
- "a mystical forest at golden hour, ethereal lighting, highly detailed"
- "cyberpunk cityscape with neon lights, rain-soaked streets"
- "floating islands in the sky, waterfalls, fantasy art"
```

**Tips:**
- Be descriptive! PyTTI works best with detailed prompts
- Click "Example Prompts" for inspiration
- Use negative prompts (optional) to avoid unwanted elements

### 3. Adjust Parameters (Optional)

**Image Settings:**
- Width/Height: Image dimensions (1024x1024 recommended for SDXL)
- Quick Sizes: Preset dimension options

**Generation Settings:**
- Steps per Scene: Number of optimization iterations (200 is good balance)
  - More steps = more refinement, but slower
  - PyTTI uses iterative optimization, not one-shot generation!
- Learning Rate: How fast the image changes (0.1 is balanced)
  - Higher = faster changes but less smooth
  - Lower = slower changes but more refined

**CLIP Guidance:**
- Cutouts: Number of image crops for CLIP analysis (40 default)
  - More cutouts = stronger guidance but slower
- Cut Power: Focus distribution (2.0 default)
  - Lower = focus on center
  - Higher = focus on edges

### 4. Generate!

Click the **🎨 Generate** button to start.

**What happens:**
1. PyTTI loads the selected models (SDXL, CLIP, etc.)
2. Initializes a random latent image
3. Iteratively refines the image over 200+ steps using CLIP guidance
4. Shows real-time progress and step counter
5. Saves the final result to `outputs/`

**During generation:**
- Watch the progress bar for real-time updates
- Step counter shows current progress
- Click **⏹️ Stop** to interrupt generation

### 5. Download Results

After generation completes:
- Preview appears in the right column
- Click **⬇️ Download** to save locally
- Click **📁 Save to Gallery** for future access (coming soon)
- Output path shows where files are saved

---

## 🎛️ Understanding Parameters

### Basic Parameters

**Width/Height**
- Image dimensions in pixels
- SDXL works best at 1024x1024
- Larger = more detail but slower and more VRAM

**Steps per Scene**
- Number of optimization iterations
- 100 = fast but less refined
- 200 = balanced (recommended)
- 300+ = high quality but slow

**Learning Rate**
- Controls optimization speed
- 0.05 = slow, smooth changes
- 0.1 = balanced (recommended)
- 0.2 = fast, more chaotic

### CLIP Parameters

**Cutouts**
- How many image crops CLIP analyzes
- 20 = fast but weaker guidance
- 40 = balanced (recommended)
- 80+ = strong guidance but slow

**Cut Power**
- How cutouts are distributed across the image
- 1.0 = evenly distributed
- 2.0 = focus on center (recommended)
- 3.0+ = strong center focus

### Advanced Parameters

**EMA Value**
- Exponential moving average for temporal smoothing
- 0.99 = balanced (recommended)
- 0.995 = smoother transitions
- Use higher values for animations

**Animation Mode**
- Off = single image
- 2D = pan/zoom animations
- 3D = depth-aware camera movements
- Video Source = rotoscoping

**Seed**
- Random seed for reproducibility
- -1 = random (different each time)
- Fixed number = reproducible results

---

## 🎯 Model Selection

### Image Models

**Stable Diffusion XL (Recommended)**
- Best balanced quality and speed
- 1024x1024 native resolution
- Great for all use cases

**Flux Schnell**
- Fastest high-quality model
- Fewer steps needed (100 vs 200)
- Excellent prompt following

**Flux Dev**
- Highest quality
- Slower than Schnell
- Best for final renders

### Depth Models (for 3D)

**Depth-Anything-V2 (Recommended)**
- State-of-the-art depth estimation
- Fast and accurate
- Best for 3D camera movements

**Marigold**
- Very high quality depth
- Slower than Depth-Anything-V2
- Best for complex scenes

**AdaBins (Legacy)**
- Original PyTTI depth model
- For backward compatibility

### CLIP Models

**SigLIP (Recommended)**
- Modern, high-quality CLIP
- Better prompt understanding
- Faster than OpenAI CLIP

**OpenCLIP ViT-H-14**
- Large, powerful model
- Excellent for complex prompts

**OpenAI CLIP ViT-L/14**
- Original CLIP
- Good general purpose

---

## 💡 Tips & Best Practices

### For Best Quality

1. **Use SDXL at 1024x1024**
   - Native resolution for best results
   - Avoid upscaling from smaller sizes

2. **Give it time**
   - 200+ steps recommended
   - PyTTI's magic happens through iteration

3. **Detailed prompts**
   - Be specific about style, lighting, atmosphere
   - Include artistic styles (oil painting, cinematic, etc.)

4. **Experiment with cutouts**
   - More cutouts = stronger CLIP guidance
   - Balance with generation time

### For Speed

1. **Use Fast Test preset**
   - 512x512 resolution
   - 100 steps
   - Good for testing prompts

2. **Flux Schnell model**
   - Faster than SDXL
   - High quality in fewer steps

3. **Reduce cutouts**
   - 20 cutouts instead of 40
   - Faster but weaker guidance

### For Animations (Coming Soon)

1. **Use High Quality 3D preset**
   - Optimized for 3D camera movements
   - Temporal smoothing enabled

2. **Higher EMA values**
   - 0.995 for smooth transitions
   - Reduces flickering

3. **More steps per frame**
   - 100+ for smooth motion
   - Balance with render time

---

## 🐛 Troubleshooting

### "Out of Memory" Error

**Solutions:**
1. Reduce resolution (1024 → 512)
2. Enable FP16 (half precision)
3. Reduce cutouts (40 → 20)
4. Close other GPU applications

### Slow Generation

**Causes:**
- High resolution (1024x1024+)
- Many cutouts (60+)
- Many steps (300+)
- CPU mode (no GPU)

**Solutions:**
1. Use Fast Test preset
2. Reduce cutouts and steps
3. Try Flux Schnell model
4. Check GPU is being used (not CPU)

### Web UI Won't Start

**Solutions:**
1. Check dependencies:
   ```bash
   pip install -r requirements-webui.txt
   ```

2. Check port is available:
   ```bash
   python -m pytti.webui --port 8080
   ```

3. Check for errors:
   ```bash
   python -m pytti.webui --verbose
   ```

### Models Won't Load

**Solutions:**
1. Check internet connection (models download first time)
2. Check disk space (models are 5-10GB)
3. Manually download models:
   ```python
   from pytti.model_loader import get_model_loader
   loader = get_model_loader()
   loader.load_diffusion_model("sdxl")
   ```

---

## 🚀 Advanced Usage

### Sharing the Web UI

Create a shareable link for remote access:

```bash
python -m pytti.webui --share
```

This creates a public Gradio link (valid for 72 hours).

**Use cases:**
- Show to clients/collaborators
- Access from another device
- Remote generation

### Custom Host/Port

```bash
# Custom port
python -m pytti.webui --port 8080

# Custom host (for Docker, etc.)
python -m pytti.webui --host 0.0.0.0 --port 7860
```

### Reproducible Results

1. Set a fixed seed (not -1)
2. Use same parameters
3. Same prompt and model

The same seed + parameters = same result!

### Batch Generation (Coming Soon)

In a future update, you'll be able to:
- Queue multiple prompts
- Generate variations
- Batch process with different settings

---

## 🔮 Coming Soon

### Phase 2 Features (Week 2)

- **Gallery Tab**
  - View all generations
  - Compare results
  - Re-run with same settings

- **Real-time Preview**
  - See image evolve during generation
  - Live loss curve visualization

- **Preset Management**
  - Save custom presets
  - Import/export presets

### Phase 3 Features (Week 3)

- **AI Rotoscoping Tab**
  - Video upload
  - SAM 2 click-and-track
  - Automatic mask propagation
  - Transform video with AI

### Phase 4 Features (Week 4)

- **3D Animation Tab**
  - Visual camera controls
  - Parametric motion builder
  - Real-time 3D preview
  - Depth visualization

---

## 📖 Additional Resources

- **Quick Start:** [QUICK_START.md](QUICK_START.md)
- **Examples:** [MODERN_USAGE_EXAMPLES.md](MODERN_USAGE_EXAMPLES.md)
- **Full Documentation:** [MODERNIZATION_README.md](MODERNIZATION_README.md)
- **UI Proposal:** [UI_PROPOSAL.md](UI_PROPOSAL.md)
- **GitHub Issues:** https://github.com/pytti-tools/pytti-core/issues

---

## 🎉 Enjoy Creating!

PyTTI's web UI makes AI video generation accessible and intuitive. Start with a preset, enter your prompt, and watch PyTTI's unique iterative optimization create distinctive, evolving visuals!

**Pro tip:** PyTTI's magic is in the journey, not just the destination. Watch how the image evolves over 200+ steps - that's what makes PyTTI special! 🎨✨
