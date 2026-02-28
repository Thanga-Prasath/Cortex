#!/bin/bash
set -e

echo "============================================================"
echo "  Cortex — Building .dmg Installer (setup.dmg)"
echo "============================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

APP_NAME="Cortex"
DMG_DIR="$PROJECT_ROOT/dist/dmg_staging"
DMG_OUTPUT="$PROJECT_ROOT/dist/setup.dmg"

# Check that the .app bundle exists
if [ ! -d "$PROJECT_ROOT/dist/Cortex.app" ]; then
    echo "ERROR: dist/Cortex.app not found. Run build_macos.sh first."
    exit 1
fi

# Clean previous build
rm -rf "$DMG_DIR"
rm -f "$DMG_OUTPUT"

echo "Creating DMG staging area..."

# Create staging directory
mkdir -p "$DMG_DIR"

# Copy .app bundle
cp -R "$PROJECT_ROOT/dist/Cortex.app" "$DMG_DIR/"

# Create symlink to /Applications for easy drag-to-install
ln -s /Applications "$DMG_DIR/Applications"

# Create auto-startup LaunchAgent plist installer script
# This runs after the user drags Cortex to Applications
cat > "$DMG_DIR/Enable Auto-Start.command" << 'SCRIPT'
#!/bin/bash
# Cortex Auto-Start Setup for macOS
# This creates a LaunchAgent to start Cortex on login

PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.cortex.voiceassistant.plist"

mkdir -p "$PLIST_DIR"

cat > "$PLIST_FILE" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cortex.voiceassistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/Cortex.app/Contents/MacOS/Cortex</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/cortex.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/cortex.err</string>
</dict>
</plist>
PLIST

# Load the agent
launchctl load "$PLIST_FILE" 2>/dev/null || true

echo ""
echo "✅ Cortex auto-start enabled!"
echo "   Cortex will start automatically on your next login."
echo ""
echo "   To disable: launchctl unload ~/Library/LaunchAgents/com.cortex.voiceassistant.plist"
echo ""
read -p "Press Enter to close..."
SCRIPT
chmod +x "$DMG_DIR/Enable Auto-Start.command"

# Create the DMG
echo ""
echo "Creating DMG disk image..."
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_DIR" \
    -ov -format UDZO \
    "$DMG_OUTPUT"

# Clean up staging
rm -rf "$DMG_DIR"

echo ""
echo "============================================================"
echo "  .dmg Created!"
echo "  Output: $DMG_OUTPUT"
echo "============================================================"
echo ""
echo "Distribution: setup.dmg"
echo "Users should:"
echo "  1. Open setup.dmg"
echo "  2. Drag Cortex to Applications"
echo "  3. Double-click 'Enable Auto-Start.command' for auto-startup"
