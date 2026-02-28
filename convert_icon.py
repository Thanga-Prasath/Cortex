#!/usr/bin/env python3
"""
Cortex Icon Converter

Converts icon.png to platform-specific icon formats:
  - icon.ico  (Windows)
  - icon.icns (macOS)

Requires: Pillow (pip install Pillow)
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("❌ Pillow is required. Install it with: pip install Pillow")
    sys.exit(1)


def convert_to_ico(src_path, dst_path):
    """Convert PNG to Windows .ico format with multiple sizes."""
    img = Image.open(src_path)
    # ICO files should contain multiple sizes for best results
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(dst_path, format='ICO', sizes=sizes)
    print(f"✅ Created {dst_path} ({os.path.getsize(dst_path) // 1024} KB)")


def convert_to_icns(src_path, dst_path):
    """Convert PNG to macOS .icns format.
    
    Note: Full .icns creation requires macOS iconutil.
    This creates a basic .icns using Pillow (limited but functional).
    For production, build on macOS and use iconutil.
    """
    img = Image.open(src_path)
    # Resize to 512x512 for the primary size
    img_resized = img.resize((512, 512), Image.LANCZOS)
    img_resized.save(dst_path, format='ICNS')
    print(f"✅ Created {dst_path} ({os.path.getsize(dst_path) // 1024} KB)")


def main():
    base_dir = Path(__file__).parent
    src = base_dir / "icon.png"
    
    if not src.exists():
        print(f"❌ Source icon not found: {src}")
        sys.exit(1)
    
    print(f"📦 Converting {src}...")
    
    # Verify it's a valid image
    img = Image.open(src)
    print(f"   Source: {img.size[0]}x{img.size[1]}, {img.mode}")
    
    # Convert to .ico (Windows)
    ico_path = base_dir / "icon.ico"
    try:
        convert_to_ico(src, ico_path)
    except Exception as e:
        print(f"⚠️  Failed to create .ico: {e}")
    
    # Convert to .icns (macOS)
    icns_path = base_dir / "icon.icns"
    try:
        convert_to_icns(src, icns_path)
    except Exception as e:
        print(f"⚠️  Failed to create .icns: {e}")
        print("   (Full .icns support requires building on macOS with iconutil)")
    
    print("\n🎉 Icon conversion complete!")


if __name__ == "__main__":
    main()
