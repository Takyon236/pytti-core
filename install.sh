#!/bin/bash

# PyTTI Installation Script
# Handles git submodules and vendor dependencies

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           PyTTI Modern - Installation Script              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Please run this script from the pytti-core directory"
    exit 1
fi

echo "📦 Step 1: Initializing git submodules..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git submodule update --init --recursive
echo "✓ Submodules initialized"
echo ""

echo "🔧 Step 2: Installing vendor dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Install AdaBins
if [ -d "vendor/AdaBins" ]; then
    echo "Installing AdaBins..."
    pip install ./vendor/AdaBins
    echo "✓ AdaBins installed"
else
    echo "⚠️  AdaBins directory not found, skipping..."
fi

# Install CLIP
if [ -d "vendor/CLIP" ]; then
    echo "Installing CLIP..."
    pip install ./vendor/CLIP
    echo "✓ CLIP installed"
else
    echo "⚠️  CLIP directory not found, skipping..."
fi

# Install GMA
if [ -d "vendor/GMA" ]; then
    echo "Installing GMA..."
    pip install ./vendor/GMA
    echo "✓ GMA installed"
else
    echo "⚠️  GMA directory not found, skipping..."
fi

# Install taming-transformers
if [ -d "vendor/taming-transformers" ]; then
    echo "Installing taming-transformers..."
    pip install ./vendor/taming-transformers
    echo "✓ taming-transformers installed"
else
    echo "⚠️  taming-transformers directory not found, skipping..."
fi

echo ""
echo "📦 Step 3: Installing PyTTI core..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Detect installation option
if [ "$1" = "all" ]; then
    echo "Installing PyTTI with ALL features (modern + webui)..."
    pip install -e ".[all]"
elif [ "$1" = "modern" ]; then
    echo "Installing PyTTI with modern AI models..."
    pip install -e ".[modern]"
elif [ "$1" = "webui" ]; then
    echo "Installing PyTTI with Web UI..."
    pip install -e ".[webui]"
else
    echo "Installing PyTTI core only..."
    echo "(Use './install.sh all' for all features)"
    pip install -e .
fi

echo "✓ PyTTI installed"
echo ""

echo "🔍 Step 4: Validating installation..."
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
