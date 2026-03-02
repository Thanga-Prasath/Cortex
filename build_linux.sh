#!/usr/bin/env bash
# ============================================================
# Cortex — Linux Local Build Script
# Builds the .deb package on this Linux machine.
# Run from project root: bash build_linux.sh
# ============================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=================================================="
echo "  Cortex Linux Build"
echo "  Project: $PROJECT_ROOT"
echo "=================================================="

# ── 1. Check prerequisites ────────────────────────────────
echo ""
echo "[Step 1] Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 not found"; exit 1; }
command -v dpkg-deb >/dev/null 2>&1 || { echo "❌ dpkg-deb not found. Install: sudo apt install dpkg"; exit 1; }
command -v rsync >/dev/null 2>&1    || { echo "❌ rsync not found. Install: sudo apt install rsync"; exit 1; }
echo "✅ Prerequisites OK"

# ── 2. Build .deb ────────────────────────────────────────
echo ""
echo "[Step 2] Building .deb package..."
bash "$PROJECT_ROOT/installer/linux/build_deb.sh"

# ── 3. Show result ───────────────────────────────────────
echo ""
DEB_FILE=$(ls "$PROJECT_ROOT"/cortex_*.deb 2>/dev/null | tail -1)
if [ -f "$DEB_FILE" ]; then
    echo "=================================================="
    echo "  ✅  Linux build complete!"
    echo "  File: $(basename "$DEB_FILE")"
    echo "  Size: $(du -sh "$DEB_FILE" | cut -f1)"
    echo "=================================================="
else
    echo "❌ .deb file not found — check build output above"
    exit 1
fi
