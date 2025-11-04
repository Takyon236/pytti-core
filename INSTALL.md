# PyTTI Installation Guide

Complete installation guide for PyTTI Modern (2025).

---

## 📋 Table of Contents

1. [Quick Install (Recommended)](#quick-install-recommended)
2. [Install Options](#install-options)
3. [Platform-Specific Instructions](#platform-specific-instructions)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Development Installation](#development-installation)

---

## 🚀 Quick Install (Recommended)

### For Most Users (Web UI + Modern AI)

```bash
# 1. Clone repository
git clone https://github.com/pytti-tools/pytti-core
cd pytti-core

# 2. Install with all modern features
pip install -e ".[all]"

# 3. Launch Web UI
pytti-webui
```

Opens browser at `http://localhost:7860` 🎉

---

## 📦 Install Options

PyTTI offers multiple installation options via extras:

### Option 1: Full Installation (Recommended)

Install everything - core, modern AI models, and Web UI:

```bash
pip install -e ".[all]"
```

**Includes:**
- Core PyTTI
- Stable Diffusion XL, Flux
- Depth-Anything-V2, SAM 2
- CoTracker, modern CLIP
- Gradio Web UI
- Development tools

### Option 2: Core + Modern AI

Install core PyTTI with modern models (no Web UI):

```bash
pip install -e ".[modern]"
```

**Includes:**
- Core PyTTI
- Stable Diffusion XL, Flux
- Depth-Anything-V2, SAM 2
- CoTracker, SigLIP

**Use if:** You want modern AI but prefer command-line

### Option 3: Core + Web UI

Install core PyTTI with Web UI (legacy models):

```bash
pip install -e ".[webui]"
```

**Includes:**
- Core PyTTI
- Gradio Web UI
- Legacy models (VQGAN, AdaBins, GMA)

**Use if:** You want the UI but don't need cutting-edge models

### Option 4: Core Only (Legacy)

Install just core PyTTI with legacy models:

```bash
pip install -e .
```

**Includes:**
- Core PyTTI
- VQGAN
- AdaBins
- GMA
- Original CLIP

**Use if:** Backward compatibility or low-resource systems

### Option 5: Individual Extras

Mix and match features:

```bash
# Core + Modern AI only
pip install -e ".[modern]"

# Core + Web UI only
pip install -e ".[webui]"

# Core + Modern + Web UI (recommended)
pip install -e ".[modern,webui]"

# Development setup
pip install -e ".[modern,webui,dev]"
```

---

## 💻 Platform-Specific Instructions

### Linux (Ubuntu/Debian)

**Prerequisites:**
```bash
# Update system
sudo apt update

# Install Python 3.8+
sudo apt install python3 python3-pip python3-venv

# Install build tools
sudo apt install build-essential

# Install FFmpeg (for video)
sudo apt install ffmpeg

# Install git
sudo apt install git
```

**Install PyTTI:**
```bash
# Create virtual environment (recommended)
python3 -m venv pytti-env
source pytti-env/bin/activate

# Clone and install
git clone https://github.com/pytti-tools/pytti-core
cd pytti-core
pip install -e ".[all]"

# Launch
pytti-webui
```

### macOS

**Prerequisites:**
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.8+
brew install python@3.10

# Install FFmpeg
brew install ffmpeg

# Install git
brew install git
```

**Install PyTTI:**
```bash
# Create virtual environment
python3 -m venv pytti-env
source pytti-env/bin/activate

# Clone and install
git clone https://github.com/pytti-tools/pytti-core
cd pytti-core
pip install -e ".[all]"

# Launch
pytti-webui
```

**Note:** M1/M2/M3 Macs use MPS (Metal Performance Shaders) for acceleration. PyTTI will automatically use MPS if available.

### Windows

**Prerequisites:**

1. **Install Python 3.8+** from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH"
   - ✅ Check "Install pip"

2. **Install Git** from [git-scm.com](https://git-scm.com/download/win)

3. **Install FFmpeg:**
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Extract to `C:\ffmpeg`
   - Add `C:\ffmpeg\bin` to PATH

4. **Install Visual C++ Build Tools** (for some dependencies)
   - Download from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Select "Desktop development with C++"

**Install PyTTI:**
```powershell
# Create virtual environment
python -m venv pytti-env
pytti-env\Scripts\activate

# Clone and install
git clone https://github.com/pytti-tools/pytti-core
cd pytti-core
pip install -e ".[all]"

# Launch
pytti-webui
```

### Docker (All Platforms)

**Coming Soon:** Docker images for easy deployment

```bash
# Future Docker install
docker pull pyttitools/pytti-core:latest
docker run -p 7860:7860 pyttitools/pytti-core
```

---

## ✅ Verification

### 1. Verify Installation

```bash
# Run validation script
pytti-validate
```

**Expected output:**
```
✓ Python 3.10.x
✓ PyTorch 2.5.0 (CUDA 12.1)
✓ GPU: NVIDIA RTX 4090 (24 GB)
✓ Diffusers 0.31.0
✓ Transformers 4.45.0
✓ Gradio 4.44.0
✓ All dependencies installed!
```

### 2. Test Web UI

```bash
# Launch Web UI
pytti-webui
```

Should open browser at `http://localhost:7860`

### 3. Test CLI

```bash
# Use a preset config
python -m pytti config/presets/sdxl_default.yaml
```

Should start generating with SDXL.

---

## 🐛 Troubleshooting

### "No module named 'pytti'"

**Solution:** Install in editable mode
```bash
pip install -e .
```

### "CUDA not available"

**Check CUDA:**
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

**If False:**
1. Install CUDA Toolkit from [nvidia.com](https://developer.nvidia.com/cuda-downloads)
2. Install PyTorch with CUDA:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```

### "Out of Memory" Error

**Solutions:**

1. **Use FP16 (half precision):**
   ```yaml
   use_fp16: true
   ```

2. **Reduce resolution:**
   ```yaml
   width: 512
   height: 512
   ```

3. **Reduce cutouts:**
   ```yaml
   cutouts: 20
   ```

4. **Check VRAM usage:**
   ```bash
   nvidia-smi
   ```

### "ModuleNotFoundError: No module named 'diffusers'"

**Solution:** Install modern extras
```bash
pip install -e ".[modern]"
```

### "Gradio not found"

**Solution:** Install Web UI extras
```bash
pip install -e ".[webui]"
```

### Slow Generation on Mac

**For M1/M2/M3 Macs:**

Check MPS is enabled:
```bash
python -c "import torch; print(torch.backends.mps.is_available())"
```

If True, PyTTI will use MPS automatically.

### FFmpeg Not Found

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Add to PATH

---

## 🔧 Development Installation

For contributors and developers:

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/pytti-tools/pytti-core
cd pytti-core

# Install in editable mode with dev tools
pip install -e ".[all,dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black src/

# Type checking
mypy src/
```

---

## 📊 System Requirements

### Minimum Requirements

- **OS:** Linux, macOS, Windows 10+
- **Python:** 3.8 or higher
- **RAM:** 8 GB
- **Storage:** 20 GB free space (for models)
- **GPU:** NVIDIA GPU with 8GB VRAM (or CPU mode)

### Recommended Requirements

- **OS:** Linux (Ubuntu 20.04+) or macOS
- **Python:** 3.10 or 3.11
- **RAM:** 16 GB+
- **Storage:** 50 GB SSD
- **GPU:** NVIDIA RTX 3060 (12GB) or better
- **CUDA:** 11.8 or 12.1

### Optimal Requirements

- **OS:** Linux (Ubuntu 22.04)
- **Python:** 3.11
- **RAM:** 32 GB+
- **Storage:** 100 GB NVMe SSD
- **GPU:** NVIDIA RTX 4090 (24GB)
- **CUDA:** 12.1

---

## 🌐 Alternative Installation Methods

### Via pip (PyPI) - Coming Soon

```bash
# Future PyPI install
pip install pyttitools-core[all]
```

### Via conda - Coming Soon

```bash
# Future conda install
conda install -c conda-forge pyttitools-core
```

---

## 📚 Next Steps

After installation:

1. **Web UI:** [WEBUI_GUIDE.md](WEBUI_GUIDE.md)
2. **Quick Start:** [QUICK_START.md](QUICK_START.md)
3. **Examples:** [MODERN_USAGE_EXAMPLES.md](MODERN_USAGE_EXAMPLES.md)
4. **Full Docs:** [MODERNIZATION_README.md](MODERNIZATION_README.md)

---

## 💡 Installation Summary

**Recommended for most users:**
```bash
git clone https://github.com/pytti-tools/pytti-core
cd pytti-core
pip install -e ".[all]"
pytti-webui
```

**That's it! You're ready to create! 🎨✨**

---

## 🆘 Getting Help

- **Validation:** `pytti-validate`
- **Documentation:** [WEBUI_GUIDE.md](WEBUI_GUIDE.md)
- **GitHub Issues:** https://github.com/pytti-tools/pytti-core/issues
- **Community:** (Discord link TBD)

---

**Made with ❤️ by the PyTTI community**
