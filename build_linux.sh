#!/bin/bash
set -e

echo "============================================================"
echo "  Cortex Desktop App — Linux Build"
echo "============================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found. Run setup.py first."
    exit 1
fi

# Install PyInstaller if not present
if ! pip show pyinstaller &>/dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Convert icons
echo ""
echo "Converting icons..."
python convert_icon.py

# Build with PyInstaller
echo ""
echo "Building Cortex with PyInstaller..."
pyinstaller cortex.spec --noconfirm

# Make the output executable
chmod +x dist/Cortex/Cortex

# Make piper executable if bundled
if [ -f "dist/Cortex/piper_engine/piper/piper" ]; then
    chmod +x dist/Cortex/piper_engine/piper/piper
fi

echo ""
echo "============================================================"
echo "  Build Complete!"
echo "  Output: dist/Cortex/Cortex"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Test:  ./dist/Cortex/Cortex"
echo "  2. Create .deb: bash installer/linux/build_deb.sh"
