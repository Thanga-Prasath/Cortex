#!/usr/bin/env bash
# ============================================================
# Cortex — Linux .deb Package Builder
# Produces: cortex_v1.0.0-beta_amd64.deb
# Run from project root: bash installer/linux/build_deb.sh
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERSION=$(cat "$PROJECT_ROOT/version.txt" | tr -d '[:space:]' | sed 's/^v//')
PKG_NAME="cortex_${VERSION}_amd64"
BUILD_DIR="/tmp/${PKG_NAME}"
INSTALL_DIR="$BUILD_DIR/opt/cortex"
DEB_OUT="$PROJECT_ROOT/${PKG_NAME}.deb"

echo "=================================================="
echo "  Cortex .deb Builder  —  version: $VERSION"
echo "=================================================="

# ── 1. Clean previous build ───────────────────────────────
rm -rf "$BUILD_DIR"
mkdir -p "$INSTALL_DIR"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/pixmaps"
mkdir -p "$BUILD_DIR/DEBIAN"

# ── 2. Copy application source files ─────────────────────
echo "[1/6] Copying application files..."
rsync -a --exclude='venv' \
         --exclude='__pycache__' \
         --exclude='*.pyc' \
         --exclude='piper_engine' \
         --exclude='data/whisper_model' \
         --exclude='dist' \
         --exclude='build' \
         --exclude='.git' \
         --exclude='*.deb' \
         --exclude='*.exe' \
         --exclude='*.spec' \
         "$PROJECT_ROOT/" "$INSTALL_DIR/"

# ── 3. Copy launcher and icon ─────────────────────────────
echo "[2/6] Setting up launcher and icon..."
chmod +x "$INSTALL_DIR/launcher.py"
cp "$PROJECT_ROOT/icon.png" "$BUILD_DIR/usr/share/pixmaps/cortex.png"

# ── 4. Create /usr/bin/cortex wrapper ─────────────────────
echo "[3/6] Creating /usr/bin/cortex launcher..."
cat > "$BUILD_DIR/usr/bin/cortex" << 'EOF'
#!/bin/bash
cd /opt/cortex
exec /opt/cortex/venv/bin/python /opt/cortex/launcher.py "$@"
EOF
chmod +x "$BUILD_DIR/usr/bin/cortex"

# ── 5. Copy .desktop file ────────────────────────────────
echo "[4/6] Installing .desktop entry..."
cp "$SCRIPT_DIR/cortex.desktop" "$BUILD_DIR/usr/share/applications/cortex.desktop"

# ── 6. DEBIAN control file ───────────────────────────────
echo "[5/6] Writing DEBIAN/control..."
INSTALLED_SIZE=$(du -sk "$INSTALL_DIR" | cut -f1)
cat > "$BUILD_DIR/DEBIAN/control" << EOF
Package: cortex
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Installed-Size: $INSTALLED_SIZE
Depends: python3 (>= 3.9), python3-pip, python3-venv, portaudio19-dev, libportaudio2
Maintainer: Thanga-Prasath <thangaprasath@github.com>
Homepage: https://github.com/Thanga-Prasath/Cortex
Description: Cortex AI Voice Assistant
 Cortex is an AI-powered voice assistant that lets you control your
 desktop, manage files, and interact via natural speech.
 .
 Large AI models (Whisper, Piper TTS) are downloaded automatically
 on first launch.
EOF

# Post-install script: setup venv + install all Python deps via pip
cat > "$BUILD_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e
echo "============================================"
echo "  Setting up Cortex — please wait..."
echo "============================================"
cd /opt/cortex

# Install system audio library if missing
if ! ldconfig -p | grep -q libportaudio; then
    apt-get install -y portaudio19-dev libportaudio2 2>/dev/null || true
fi

# Create venv and install Python packages
if [ ! -d "venv" ]; then
    echo "[1/3] Creating Python virtual environment..."
    python3 -m venv venv

    echo "[2/3] Installing Python dependencies (this may take 2-3 minutes)..."
    venv/bin/pip install --upgrade pip --quiet

    if [ -f requirements-linux.txt ]; then
        venv/bin/pip install -r requirements-linux.txt
    fi
    echo "[3/3] Done!"
fi

chmod +x /opt/cortex/launcher.py
update-desktop-database /usr/share/applications/ 2>/dev/null || true
echo "============================================"
echo "  ✅ Cortex is ready! Run: cortex"
echo "============================================"
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# Post-remove script
cat > "$BUILD_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e
if [ "$1" = "purge" ]; then
    rm -rf /opt/cortex
fi
update-desktop-database /usr/share/applications/ 2>/dev/null || true
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# ── 7. Build .deb ────────────────────────────────────────
echo "[6/6] Building .deb package..."
dpkg-deb --build "$BUILD_DIR" "$DEB_OUT"

echo ""
echo "=================================================="
echo "  ✅ Package ready: $(basename "$DEB_OUT")"
du -sh "$DEB_OUT" | awk '{print "  Size: " $1}'
echo "=================================================="
echo ""
echo "Install with:"
echo "  sudo dpkg -i $(basename "$DEB_OUT")"
echo "  sudo apt-get install -f   # fix any missing deps"
