#!/usr/bin/env python3
"""
Test script for new window control features:
1. Switch to specific app window (window_switch_to)
2. Tile all windows in grid (window_show_all)

Run from your terminal:
    python test_new_window_features.py
"""
import subprocess
import shutil
import platform
import time
import os

current_os = platform.system()

def banner(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

# =============================================
#  Test Helper Functions
# =============================================

def test_extract_app_name():
    """Test app name extraction from voice commands."""
    banner("TEST 1: App Name Extraction")

    test_cases = [
        ("switch to firefox", "firefox"),
        ("go to chrome", "chrome"),
        ("focus on terminal", "terminal"),
        ("bring up file manager", "file manager"),
        ("switch to Firefox window", "firefox"),
        ("activate vscode", "vscode"),
        ("show me nautilus app", "nautilus"),
    ]

    # Import the extraction logic
    prefixes = [
        "switch to ", "go to ", "focus on ", "bring up ",
        "show me ", "activate ", "open ", "focus "
    ]

    passed = 0
    for command, expected in test_cases:
        command_lower = command.lower().strip()
        result = ""
        for prefix in prefixes:
            if command_lower.startswith(prefix):
                result = command_lower[len(prefix):].strip()
                for suffix in [" window", " app", " application"]:
                    if result.endswith(suffix):
                        result = result[:-len(suffix)].strip()
                break
        if not result:
            words = command_lower.split()
            stop_words = {'the', 'a', 'an', 'to', 'on', 'my', 'please', 'window', 'app'}
            meaningful = [w for w in words if w not in stop_words]
            result = meaningful[-1] if meaningful else ""

        status = "✅" if result == expected else "❌"
        if status == "✅":
            passed += 1
        print(f"  {status} '{command}' → '{result}' (expected: '{expected}')")

    print(f"\n  Result: {passed}/{len(test_cases)} passed")

def test_is_app_running():
    """Test if app running detection works."""
    banner("TEST 2: App Running Detection")

    # Test with apps that should be running
    running_apps = ["python", "bash"]  # these should be running
    not_running = ["nonexistent_app_xyz123"]

    for app in running_apps:
        try:
            if current_os == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {app}*"],
                    capture_output=True, text=True, timeout=5
                )
                is_running = app.lower() in result.stdout.lower()
            else:
                result = subprocess.run(
                    ["pgrep", "-fi", app],
                    capture_output=True, text=True, timeout=5
                )
                is_running = result.returncode == 0
            status = "✅" if is_running else "❌"
            print(f"  {status} '{app}' detected as {'running' if is_running else 'NOT running'}")
        except Exception as e:
            print(f"  ❌ Error checking '{app}': {e}")

    for app in not_running:
        try:
            if current_os == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {app}*"],
                    capture_output=True, text=True, timeout=5
                )
                is_running = app.lower() in result.stdout.lower()
            else:
                result = subprocess.run(
                    ["pgrep", "-fi", app],
                    capture_output=True, text=True, timeout=5
                )
                is_running = result.returncode == 0
            status = "✅" if not is_running else "❌"
            print(f"  {status} '{app}' correctly detected as {'NOT running' if not is_running else 'running (unexpected!)'}")
        except Exception as e:
            print(f"  ❌ Error checking '{app}': {e}")

def test_switch_to_app():
    """Test switching to a running application (interactive)."""
    banner("TEST 3: Switch To App (Interactive)")

    print("  This test will try to switch to 'Files' (nautilus).")
    print("  Make sure Files/Nautilus is open.")
    input("  Press Enter to proceed...")

    app_name = "nautilus"

    # Check if running
    result = subprocess.run(
        ["pgrep", "-fi", app_name],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode != 0:
        print(f"  ❌ {app_name} is not running. Open it first and try again.")
        return

    print(f"  ✅ {app_name} is running (PID: {result.stdout.strip()})")

    # Try wmctrl
    if shutil.which("wmctrl"):
        print("  Trying wmctrl -a ...")
        r = subprocess.run(["wmctrl", "-a", app_name],
                          capture_output=True, text=True, timeout=5)
        print(f"  wmctrl result: exit={r.returncode}, stderr={r.stderr.strip()}")
    else:
        print("  ⚠️ wmctrl not installed")

    # Try xdotool
    if shutil.which("xdotool"):
        print("  Trying xdotool search --name ...")
        r = subprocess.run(["xdotool", "search", "--name", app_name],
                          capture_output=True, text=True, timeout=5)
        ids = r.stdout.strip().split('\n')
        print(f"  xdotool found window IDs: {ids}")
        if ids and ids[0]:
            subprocess.run(["xdotool", "windowactivate", ids[0]], timeout=5)
    else:
        print("  ⚠️ xdotool not installed")

    # Try gtk-launch
    print("  Trying gtk-launch ...")
    r = subprocess.run(["gtk-launch", f"org.gnome.Nautilus"],
                      capture_output=True, text=True, timeout=5)
    print(f"  gtk-launch result: exit={r.returncode}")

    print("\n  → Did Files/Nautilus come to focus?")

def test_tile_all():
    """Test tiling all windows (interactive)."""
    banner("TEST 4: Tile All Windows (Interactive)")

    if current_os == "Linux":
        if shutil.which("wmctrl"):
            print("  wmctrl is available — will try grid tiling")
            result = subprocess.run(["wmctrl", "-l"],
                                   capture_output=True, text=True, timeout=5)
            print(f"  Window list:\n{result.stdout}")

            if result.stdout.strip():
                print("\n  Tiling in 3 seconds...")
                time.sleep(3)

                import math
                lines = [l for l in result.stdout.strip().split('\n')]
                n = len(lines)
                screen_w, screen_h = 1920, 1080  # default

                # Try to get actual screen size
                try:
                    desk = subprocess.run(["wmctrl", "-d"],
                                         capture_output=True, text=True, timeout=3)
                    for part in desk.stdout.split():
                        if 'x' in part and part.replace('x', '').isdigit():
                            w, h = part.split('x')
                            screen_w, screen_h = int(w), int(h)
                            break
                except Exception:
                    pass

                cols = math.ceil(math.sqrt(n))
                rows = math.ceil(n / cols)
                cell_w = screen_w // cols
                cell_h = screen_h // rows

                print(f"  Grid: {cols}x{rows}, Cell: {cell_w}x{cell_h}, Screen: {screen_w}x{screen_h}")

                for i, line in enumerate(lines):
                    win_id = line.split()[0]
                    col = i % cols
                    row = i // cols
                    x = col * cell_w
                    y = row * cell_h
                    subprocess.run(
                        ["wmctrl", "-ir", win_id, "-e", f"0,{x},{y},{cell_w},{cell_h}"],
                        timeout=3
                    )
                    print(f"  Moved {win_id} to ({x},{y}) {cell_w}x{cell_h}")

                print(f"\n  ✅ Tiled {n} windows!")
            else:
                print("  ❌ No windows found via wmctrl")
        else:
            print("  ⚠️ wmctrl not installed — will use Activities Overview")
            print("  Pressing Super key in 3 seconds...")
            time.sleep(3)
            try:
                from evdev import UInput, ecodes
                caps = {ecodes.EV_KEY: list(range(0, 256))}
                ui = UInput(caps, name='cortex-test-kbd')
                time.sleep(0.5)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, 1)
                ui.syn()
                time.sleep(0.1)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, 0)
                ui.syn()
                time.sleep(0.1)
                ui.close()
                print("  ✅ Super key sent — Activities Overview should be showing")
            except Exception as e:
                print(f"  ❌ evdev error: {e}")
    else:
        print(f"  Testing on {current_os} using pywinctl...")
        try:
            import pywinctl
            windows = pywinctl.getAllWindows()
            print(f"  Found {len(windows)} windows:")
            for w in windows[:10]:
                print(f"    - {w.title}")
        except ImportError:
            print("  ❌ pywinctl not installed")

if __name__ == "__main__":
    print("=" * 60)
    print("  NEW WINDOW FEATURES TEST")
    print(f"  Platform: {current_os}")
    print("=" * 60)

    test_extract_app_name()
    test_is_app_running()

    choice = input("\nRun interactive tests (switch-to/tile)? [y/n]: ").strip().lower()
    if choice == 'y':
        test_switch_to_app()
        test_tile_all()
    else:
        print("Skipping interactive tests.")

    print("\n" + "=" * 60)
    print("  TESTS COMPLETE")
    print("=" * 60)
