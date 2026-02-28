#!/bin/bash
set -e

echo "============================================================"
echo "  Cortex Desktop App — macOS Build"
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

echo ""
echo "============================================================"
echo "  Build Complete!"
echo "  Output: dist/Cortex.app"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Test: open dist/Cortex.app"
echo "  2. Create .dmg: bash installer/macos/build_dmg.sh"
