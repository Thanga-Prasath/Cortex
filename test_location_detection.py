#!/usr/bin/env python3
"""
Test script to verify active location detection.
Run this with a file manager window open to see if it detects the correct path.
"""

import sys
sys.path.append("/media/silver/software/Final Year Project/Sunday-manual")

from core.engines.file_manager import FileManagerEngine
from core.speaking import Speaker

# Create engine
speaker = Speaker()
engine = FileManagerEngine(speaker)

# Test location detection
print("\n" + "="*60)
print("TESTING ACTIVE LOCATION DETECTION")
print("="*60)
print("\nPlease open a file manager window to a specific folder")
print("(e.g., Downloads, Documents, /tmp, etc.)")
print("\nPress Enter when ready...")
input()

detected_location = engine._get_active_location()

print("\n" + "="*60)
print(f"DETECTED LOCATION: {detected_location}")
print("="*60)

# Verify it's not just defaulting to Desktop
if detected_location == engine.desktop_path:
    print("\n⚠️  WARNING: Defaulted to Desktop")
    print("This might mean:")
    print("  - No file manager window is open")
    print("  - The file manager is not supported")
    print("  - Detection methods failed")
else:
    print("\n✅ SUCCESS: Detected a specific location!")
    print(f"   Location: {detected_location}")

print("\n" + "="*60)
