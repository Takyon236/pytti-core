#!/bin/bash

# PyTTI Modern Installation Script
# No legacy dependencies required - uses modern AI models only

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           PyTTI Modern - Installation Script              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  IMPORTANT: Install PyTorch first for your CUDA version!"
echo "Visit: https://pytorch.org/get-started/locally/"
echo ""
echo "Example for CUDA 12.1:"
echo "  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Please run this script from the pytti-core directory"
    exit 1
fi

echo "📦 Installing PyTTI Modern..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Detect installation option
if [ "$1" = "all" ]; then
    echo "Installing PyTTI with ALL features (modern + webui)..."
    echo "Using version constraints for stable, tested dependencies..."
    pip install -c constraints.txt -e ".[all]"
elif [ "$1" = "modern" ]; then
    echo "Installing PyTTI with modern AI models..."
    echo "Using version constraints for stable, tested dependencies..."
    pip install -c constraints.txt -e ".[modern]"
elif [ "$1" = "webui" ]; then
    echo "Installing PyTTI with Web UI..."
    echo "Using version constraints for stable, tested dependencies..."
    pip install -c constraints.txt -e ".[webui]"
else
    echo "Installing PyTTI core only..."
    echo "(Use './install.sh all' for all features)"
    echo "Using version constraints for stable, tested dependencies..."
    pip install -c constraints.txt -e .
fi

echo "✓ PyTTI installed"
echo ""

echo "🔍 Validating installation..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v pytti-validate &> /dev/null; then
    pytti-validate
else
    echo "⚠️  pytti-validate not found, skipping validation..."
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ Installation Complete! ✅                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ "$1" = "all" ] || [ "$1" = "webui" ]; then
    echo "🚀 Launch Web UI with:"
    echo "   pytti-webui"
    echo ""
fi

echo "📚 Documentation:"
echo "   • Quick Start: QUICK_START.md"
echo "   • Web UI Guide: WEBUI_GUIDE.md"
echo "   • Examples: MODERN_USAGE_EXAMPLES.md"
echo ""
echo "🎨 Happy creating!"
