#!/bin/bash
# Complete PyTTI-Core Installation Script for Python 3.12
# This installs everything needed for the webui

set -e  # Exit on error

echo "=== PyTTI-Core Complete Installation ==="
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install core dependencies
echo ""
echo "Step 1/4: Installing core dependencies..."
pip install -r requirements.txt

# Install modern AI dependencies
echo ""
echo "Step 2/4: Installing modern AI dependencies (Stable Diffusion, Flux)..."
pip install -r requirements-modern.txt

# Install webui dependencies
echo ""
echo "Step 3/4: Installing webui dependencies (Gradio)..."
pip install -r requirements-webui.txt

# Install taming-transformers for VQGAN
echo ""
echo "Step 4/4: Installing VQGAN support..."
pip install taming-transformers-rom1504

# Install pytti-core in editable mode
echo ""
echo "Installing pytti-core..."
pip install -e .

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "To run the webui:"
echo "  pytti-webui"
echo ""
echo "Optional features (install separately if needed):"
echo "  pip install pyttitools-gma      # Optical flow"
echo "  pip install pyttitools-adabins  # Depth estimation"
echo ""
