#!/bin/bash
set -e

echo "============================================================"
echo "  Cortex — Building .deb Package (setup.deb)"
echo "============================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

VERSION="1.0.0"
ARCH="amd64"
PKG_NAME="cortex"
PKG_DIR="$PROJECT_ROOT/dist/${PKG_NAME}_${VERSION}_${ARCH}"

# Check that the PyInstaller build exists
if [ ! -d "$PROJECT_ROOT/dist/Cortex" ]; then
    echo "ERROR: dist/Cortex/ not found. Run build_linux.sh first."
    exit 1
fi

# Clean previous build
rm -rf "$PKG_DIR"

echo "Creating package structure..."

# Create directory structure
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/cortex"
mkdir -p "$PKG_DIR/usr/local/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$PKG_DIR/etc/xdg/autostart"

# Copy application files
echo "Copying application files..."
cp -r "$PROJECT_ROOT/dist/Cortex/"* "$PKG_DIR/opt/cortex/"

# Create symlink for /usr/local/bin
ln -sf /opt/cortex/Cortex "$PKG_DIR/usr/local/bin/cortex"

# Copy desktop file (for application menu)
cp "$SCRIPT_DIR/cortex.desktop" "$PKG_DIR/usr/share/applications/"

# Copy autostart desktop file (auto-startup on login)
cat > "$PKG_DIR/etc/xdg/autostart/cortex-autostart.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Cortex
Comment=AI Voice Assistant - Auto Start
Exec=/opt/cortex/Cortex
Icon=cortex
Terminal=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

# Copy icon
if [ -f "$PROJECT_ROOT/icon.png" ]; then
    cp "$PROJECT_ROOT/icon.png" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/cortex.png"
fi

# Create control file
cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: cortex
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: libportaudio2, libxcb-xinerama0
Installed-Size: $(du -sk "$PKG_DIR/opt" | cut -f1)
Maintainer: Cortex Project
Description: Cortex AI Voice Assistant
 A standalone AI voice assistant with speech recognition,
 natural language understanding, and text-to-speech capabilities.
 Features include system management, file operations, automation,
 and workspace management. Auto-starts on login.
Homepage: https://github.com/Thanga-Prasath/Cortex
EOF

# Create postinst script (set permissions after install)
cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
chmod +x /opt/cortex/Cortex
# Make piper executable if present
if [ -f "/opt/cortex/piper_engine/piper/piper" ]; then
    chmod +x /opt/cortex/piper_engine/piper/piper
fi
# Update desktop database
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi
# Update icon cache
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
fi
echo ""
echo "✅ Cortex installed successfully!"
echo "   Cortex will auto-start on your next login."
echo "   To disable auto-start: remove /etc/xdg/autostart/cortex-autostart.desktop"
echo ""
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# Create postrm script (cleanup on removal)
cat > "$PKG_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
# Clean up autostart on removal
rm -f /etc/xdg/autostart/cortex-autostart.desktop 2>/dev/null || true
# Update desktop database
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi
EOF
chmod 755 "$PKG_DIR/DEBIAN/postrm"

# Build the .deb package
echo ""
echo "Building .deb package..."
dpkg-deb --build "$PKG_DIR"

# Rename to setup.deb
DEB_OUTPUT="$PROJECT_ROOT/dist/${PKG_NAME}_${VERSION}_${ARCH}.deb"
FINAL_OUTPUT="$PROJECT_ROOT/dist/setup.deb"
mv "$DEB_OUTPUT" "$FINAL_OUTPUT"

echo ""
echo "============================================================"
echo "  .deb Package Created!"
echo "  Output: $FINAL_OUTPUT"
echo "============================================================"
echo ""
echo "Install with:  sudo dpkg -i dist/setup.deb"
echo "Remove with:   sudo apt remove cortex"
echo ""
echo "Auto-startup: Cortex will start automatically on login."
echo "Disable with: sudo rm /etc/xdg/autostart/cortex-autostart.desktop"
