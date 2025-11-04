# PyTTI-Tools: Core
[![Jupyter Book Badge](https://jupyterbook.org/badge.svg)](https://pytti-tools.github.io/pytti-book/intro.html)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pytti-tools/pytti-notebook/blob/main/pyttitools-PYTTI.ipynb)
[![DOI](https://zenodo.org/badge/452409075.svg)](https://zenodo.org/badge/latestdoi/452409075)

---

## 🎉 PyTTI Modernization 2025 - Now Available!

**PyTTI has been modernized with 2025 state-of-the-art AI models while preserving its unique aesthetic!**

### ✨ What's New

- 🖼️ **Modern Image Models:** Stable Diffusion XL, Flux (replaces VQGAN)
- 🔍 **Modern Depth:** Depth-Anything-V2, Marigold (replaces AdaBins)
- 🎭 **AI Rotoscoping:** SAM 2 auto-tracking (click once, segment entire video!)
- 🌊 **Modern Optical Flow:** CoTracker, RAFT (enhanced from GMA)
- 🌐 **Browser-Based Web UI:** Intuitive Gradio interface (no command line needed!)
- ⚙️ **Smart Presets:** One-click configurations for common use cases
- 📚 **Comprehensive Docs:** 4,000+ lines of guides and examples

### 🚀 Quick Start (Web UI - Recommended)

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -r requirements-modern.txt
pip install -r requirements-webui.txt

# 2. Launch browser interface
python -m pytti.webui

# Opens at http://localhost:7860
# Select preset, enter prompt, click Generate! 🎨
```

### 📖 Documentation

- **[QUICK_START.md](QUICK_START.md)** - 5-minute beginner guide
- **[WEBUI_GUIDE.md](WEBUI_GUIDE.md)** - Complete Web UI manual
- **[MODERNIZATION_COMPLETE.md](MODERNIZATION_COMPLETE.md)** - Full project summary
- **[MODERN_USAGE_EXAMPLES.md](MODERN_USAGE_EXAMPLES.md)** - 10 detailed examples
- **[MODERNIZATION_README.md](MODERNIZATION_README.md)** - Technical overview

### 🎯 What Was Preserved

PyTTI's distinctive "flavor" remains intact:
- ✅ Iterative CLIP-guided optimization (200+ steps of refinement)
- ✅ Depth-aware 3D camera movements with parametric motion
- ✅ Rotoscoping orchestrator for multi-layer video transformation
- ✅ EMA temporal smoothing for stable animations
- ✅ All original algorithms and aesthetic

**Result:** Modern AI capabilities with PyTTI's unique iterative aesthetic! 🌟

---

# Legacy Setup (Original PyTTI)

The information below describes the original PyTTI setup. For the modern version, see the Quick Start above.

## Requirements

* Python 3.x
* [Pytorch](https://pytorch.org/get-started/locally/)
* CUDA-capable GPU
* OpenCV
* ffmpeg
* Python Image Library (PIL/pillow)
* git - simplifies downloading code and keeping it up to date
* gdown - simplifies downloading pretrained models
* jupyter - (Optional) Notebook interface

# Documentation

Detailed setup and usage instructions can be found here: https://pytti-tools.github.io/pytti-book/intro.html

# Setup

(2023) this works for the moment

```
git clone --recurse-submodules -j8 https://github.com/pytti-tools/pytti-core
pip install -r pytti-core/requirements.txt
pip install ./pytti-core/vendor/AdaBins
pip install ./pytti-core/vendor/CLIP
pip install ./pytti-core/vendor/GMA
pip install ./pytti-core/vendor/taming-transformers
pip install ./pytti-core
```

you're probably gonna get an error about a missing adabins checkpoint now. Download that from here and put it in the file path corresponding to the error (should be an `adabins` subfolder of your user cache that you'll probably need to mkdir):

```
wget https://github.com/hithereai/deforum-for-automatic1111-webui/releases/download/AdaBins/AdaBins_nyu.pt
```

# Development

* Rebuild, reinstall, and run tests:
    ```
    pip uninstall -y pyttitools-core; rm -rf build; pip install .
    python -m pytest --ignore=vendor -v -s
    ```
