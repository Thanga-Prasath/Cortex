import sys
import os
import time
import subprocess
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from core.engines.file_manager import FileManagerEngine

class MockSpeaker:
    def speak(self, text):
        print(f"Speaker: {text}")

def main():
    print("Initializing FileManagerEngine...")
    engine = FileManagerEngine(MockSpeaker())
    
    print("\nIMPORTANT: Please switch focus to your File Manager window now!")
    for i in range(5, 0, -1):
        print(f"Capturing in {i} seconds...", end='\r', flush=True)
        time.sleep(1)
    print("\nCapturing now...\n")
    
    # Debug Hyprctl directly
    print("--- RAW HYPRCTL OUTPUT ---")
    try:
        output = subprocess.check_output(['hyprctl', 'activewindow', '-j'], stderr=subprocess.STDOUT)
        print(output.decode('utf-8'))
    except Exception as e:
        print(f"hyprctl failed: {e}")

    print("\n--- ENGINE LOGIC ---")
    
    print("Testing _get_active_window_hyprland directly:")
    hypr_title = engine._get_active_window_hyprland()
    print(f"Hyprland Title: '{hypr_title}'")

    title = engine._get_active_window_title()
    print(f"Engine Combined Title: '{title}'")
    
    location = engine._get_active_location()
    print(f"Engine Detected Location: {location}")

if __name__ == "__main__":
    main()
