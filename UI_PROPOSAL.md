# PyTTI UI Proposals - Making PyTTI Visual

Current situation: PyTTI uses command-line + YAML configs. This is powerful but not intuitive for a creative visual tool. Here are UI options ranked from easiest to most advanced.

---

## 🏆 Recommended: Gradio Web UI

### Why Gradio?

**Perfect for PyTTI because:**
- ✅ Browser-based (works everywhere, no install)
- ✅ Built for AI/ML tools (handles long-running tasks)
- ✅ Real-time preview (can show generation progress)
- ✅ Easy to implement (hours, not weeks)
- ✅ Shareable (can host and share links)
- ✅ Good parameter organization (tabs, accordions)
- ✅ Image/video gallery support
- ✅ Python-native (no frontend coding needed)

**What it would look like:**

```
┌─────────────────────────────────────────────────────┐
│  PyTTI Modern - AI Video Generation                 │
├─────────────────────────────────────────────────────┤
│  [Generation] [3D Animation] [Rotoscoping] [Gallery]│
├───────────────────────┬─────────────────────────────┤
│  SETTINGS             │  PREVIEW                     │
│                       │                              │
│  Model: [SDXL    ▼]  │  [Generated Image/Video]     │
│  Prompt: [______]     │                              │
│  Width:  [1024   ]    │  Step: 45/200               │
│  Height: [1024   ]    │  ████████░░░░░░░░ 45%       │
│                       │                              │
│  Advanced ▼           │  [Pause] [Stop] [Save]      │
│  - Steps: [200  ]     │                              │
│  - LR: [0.1     ]     │                              │
│  - Cutouts: [40 ]     │                              │
│                       │                              │
│  [Generate] [Queue]   │  [Download] [Add to Gallery] │
└───────────────────────┴─────────────────────────────┘
```

### Features:

**Tab 1: Text-to-Image/Video**
- Model selection (SDXL, Flux, legacy)
- Prompt input
- Basic parameters (size, steps, learning rate)
- Advanced parameters (collapsible)
- Preset selection
- Real-time preview
- Progress bar

**Tab 2: 3D Animation**
- All text-to-video features +
- Camera controls (translate X/Y/Z, rotate)
- Depth model selection
- Parametric motion helper
- FOV, near/far plane
- Real-time 3D preview

**Tab 3: AI Rotoscoping**
- Video upload
- SAM 2 segmentation interface
- Point/box click tool
- Auto-track preview
- Mask refinement
- Transformation prompt
- Frame-by-frame preview

**Tab 4: Gallery**
- Grid of generated images/videos
- Metadata (prompt, settings)
- Re-run with same settings
- Compare generations
- Export project

### Implementation Time:
- **Basic version**: 1-2 days
- **Full-featured**: 1 week
- **Polish**: 2 weeks

---

## 🎨 Alternative 1: ComfyUI-Style Workflow

### Why ComfyUI-style?

**For power users:**
- ✅ Visual node graph (intuitive for complex pipelines)
- ✅ Modular (connect components flexibly)
- ✅ Reusable workflows (save/load)
- ✅ Industry standard (Stable Diffusion users know it)
- ✅ Powerful (can create complex multi-step pipelines)

**What it would look like:**

```
┌──────────────────────────────────────────────────────────┐
│  PyTTI Workflow Editor                                    │
├──────────────────────────────────────────────────────────┤
│  [File] [Edit] [View] [Help]    [▶ Run] [⏸ Pause] [⏹ Stop]│
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────┐      ┌─────────────┐    ┌────────────┐ │
│  │ Text Input │─────▶│ SDXL Model  │───▶│  Preview   │ │
│  │ "prompt"   │      │ width: 1024 │    │ [image]    │ │
│  └────────────┘      │ steps: 200  │    └────────────┘ │
│                      └─────────────┘           │        │
│                            │                   │        │
│  ┌────────────┐           │                   ▼        │
│  │ Depth      │           │           ┌────────────┐   │
│  │ Anything   │◀──────────┘           │   Save     │   │
│  │ V2         │                       │   Output   │   │
│  └────────────┘                       └────────────┘   │
│       │                                                 │
│       ▼                                                 │
│  ┌────────────┐      ┌─────────────┐                  │
│  │  3D        │─────▶│  Optical    │                  │
│  │ Transform  │      │  Flow       │                  │
│  └────────────┘      └─────────────┘                  │
│                                                         │
└──────────────────────────────────────────────────────┘
```

### Features:

**Nodes:**
- Input nodes (text, image, video, parameters)
- Model nodes (SDXL, Flux, VQGAN, Depth, SAM 2)
- Transform nodes (3D, 2D, optical flow)
- Loss nodes (CLIP, depth, flow, semantic)
- Output nodes (preview, save, video encode)

**Workflows:**
- Save/load custom workflows
- Share workflows (JSON)
- Template workflows (3D animation, rotoscoping, etc.)
- Real-time execution
- Node debugging (see intermediate results)

### Implementation Time:
- **Basic version**: 2-3 weeks
- **Full-featured**: 1-2 months
- **Polish**: 2-3 months

### Technology:
- Use existing libraries: ComfyUI, ReactFlow, or Litegraph.js
- Or: PyTTI-specific nodes in ComfyUI directly

---

## 🖥️ Alternative 2: Native Desktop App (Electron/Tauri)

### Why Native?

**For offline/professional use:**
- ✅ No browser needed
- ✅ Better performance
- ✅ File system integration
- ✅ Professional feel
- ✅ GPU optimization

**What it would look like:**

```
┌─────────────────────────────────────────────────────────┐
│ ● ● ●  PyTTI Studio                        [−][□][×]    │
├─────────────────────────────────────────────────────────┤
│ [File] [Edit] [Generate] [View] [Help]                  │
├──────────┬──────────────────────────────────────────────┤
│ Projects │  Main Canvas                                 │
│          │                                               │
│ ├─ My    │  ╔═══════════════════════════════════════╗  │
│ │  Works │  ║                                       ║  │
│ │        │  ║        [Generated Image]              ║  │
│ ├─ 3D    │  ║                                       ║  │
│ │  Anims │  ║                                       ║  │
│ │        │  ╚═══════════════════════════════════════╝  │
│ └─ Roto  │                                               │
│   scopes │  Timeline: [▬▬▬▬▬▬▬▬▬░░░░░░░░░] Frame 45/200│
│          │                                               │
├──────────┤  ┌─────────────────────────────────────┐    │
│ Settings │  │ Prompt: "mystical forest..."       │    │
│          │  │ Model: SDXL                         │    │
│ Model    │  │ Steps: 200  LR: 0.1                │    │
│ [SDXL ▼] │  └─────────────────────────────────────┘    │
│          │                                               │
│ Params   │  [▶ Generate] [⏸ Pause] [💾 Save]           │
│ [......] │                                               │
└──────────┴───────────────────────────────────────────────┘
```

### Features:
- Project management
- Timeline for video
- Real-time preview
- File browser integration
- Drag-and-drop
- Keyboard shortcuts
- GPU monitoring
- Render queue

### Implementation Time:
- **Basic version**: 3-4 weeks
- **Full-featured**: 2-3 months
- **Polish**: 3-6 months

---

## 📱 Alternative 3: Streamlit Dashboard

### Why Streamlit?

**For data-centric view:**
- ✅ Python-native
- ✅ Reactive updates
- ✅ Good for parameters/metrics
- ✅ Easy charts/graphs

**Cons:**
- ⚠️ Full page reloads (not ideal for real-time)
- ⚠️ Less suited for creative tools
- ⚠️ Not as polished for image/video generation

### Use case:
Better for monitoring/analytics than creative work. Good for showing loss curves, comparing runs, A/B testing.

### Implementation Time:
- **Basic version**: 1-2 days
- **Full-featured**: 1 week

---

## 📓 Alternative 4: Jupyter Notebook Interface

### Why Jupyter?

**For researchers/experimenters:**
- ✅ Already familiar to ML users
- ✅ Code + output in one place
- ✅ Easy to document
- ✅ Interactive widgets

**Example:**
```python
import pytti_widgets as pw

# Interactive UI in notebook
ui = pw.PyTTIStudio()
ui.prompt = "mystical forest"
ui.model = "sdxl"
ui.steps = 200

# Displays interactive widget with sliders, dropdowns, preview
ui.render()
```

**Cons:**
- Requires Jupyter
- Not standalone
- Less polished than web UI

### Implementation Time:
- **Basic version**: 2-3 days
- **Full-featured**: 1 week

---

## 🎯 Recommendation: Start with Gradio

### Why?

1. **Quick to build** - Can have basic version in 1-2 days
2. **Feature-rich** - Real-time preview, galleries, progress bars
3. **User-friendly** - Works in browser, no install
4. **Shareable** - Can host and share
5. **Expandable** - Can add ComfyUI-style nodes later

### Roadmap:

**Phase 1: Basic Gradio UI (Week 1)**
- Simple text-to-image interface
- Model selection
- Basic parameters
- Image preview
- Download output

**Phase 2: Advanced Features (Week 2)**
- 3D animation tab
- Real-time progress
- Preset selection
- Gallery system

**Phase 3: AI Rotoscoping (Week 3)**
- Video upload
- SAM 2 interface
- Point/box click
- Mask preview

**Phase 4: Polish (Week 4)**
- Better styling
- Keyboard shortcuts
- Project save/load
- Comparison tools

**Phase 5: Advanced (Later)**
- ComfyUI-style workflow (optional)
- Node graph editor
- Custom pipelines

---

## 💻 Technical Stack for Gradio

```python
# Core
gradio>=4.0.0
plotly>=5.0.0  # For charts
opencv-python>=4.0.0  # For video preview

# Optional
gradio_client>=0.7.0  # For API access
fastapi>=0.100.0  # For custom endpoints
```

### Architecture:

```
PyTTI Gradio UI
├── app.py (main interface)
├── tabs/
│   ├── generate.py (text-to-image/video)
│   ├── animation_3d.py (3D camera movements)
│   ├── rotoscope.py (AI segmentation)
│   └── gallery.py (outputs management)
├── components/
│   ├── model_selector.py
│   ├── parameter_panel.py
│   ├── preview.py (real-time)
│   └── progress.py
└── utils/
    ├── queue.py (generation queue)
    ├── preview.py (intermediate steps)
    └── storage.py (outputs)
```

---

## 🎨 UI Design Philosophy

### For PyTTI specifically:

1. **Show the iterative process**
   - PyTTI refines over time, show that!
   - Frame-by-frame preview
   - Loss curve visualization

2. **Emphasize temporal coherence**
   - Timeline scrubbing
   - Before/after comparisons
   - Optical flow visualization

3. **Make 3D intuitive**
   - Visual camera controls
   - Depth map overlay
   - Parametric motion builder

4. **Rotoscoping workflow**
   - Click-and-track interface
   - Mask refinement tools
   - Frame navigation

---

## 🚀 My Recommendation

**Start with Gradio**, then optionally add ComfyUI-style workflows later.

**Rationale:**
1. PyTTI is a creative tool → needs visual UI
2. Gradio is fastest to implement
3. Works everywhere (browser)
4. Can iterate quickly based on feedback
5. Can add advanced features incrementally

**Implementation Priority:**
```
Week 1: Basic Gradio UI ✅ (HIGH PRIORITY)
Week 2: Real-time preview + gallery
Week 3: AI rotoscoping interface
Week 4: 3D animation controls
Later: ComfyUI-style workflows (optional, for power users)
```

**Shall I start implementing the Gradio UI?** 🎨
