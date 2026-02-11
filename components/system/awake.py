import subprocess
import os
import sys
import psutil
import platform

# Path to the auxiliary script we will create
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "keep_awake_script.py")

def enable_keep_awake(speaker):
    # Check if already running
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'keep_awake_script.py' in " ".join(proc.info['cmdline']):
                speaker.speak("Keep awake mode is already active.")
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Ensure script exists
    if not os.path.exists(SCRIPT_PATH):
        # Create it dynamically if missing
        _create_awake_script()

    # Launch background process
    try:
        if platform.system() == 'Windows':
            subprocess.Popen([sys.executable, SCRIPT_PATH], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.Popen([sys.executable, SCRIPT_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        speaker.speak("I am keeping the computer awake now.")
    except Exception as e:
        speaker.speak(f"Failed to enable keep awake: {e}")

def disable_keep_awake(speaker):
    killed = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'keep_awake_script.py' in " ".join(proc.info['cmdline']):
                proc.kill()
                killed = True
        except:
            pass
    
    if killed:
        speaker.speak("Keep awake mode disabled.")
    else:
        speaker.speak("Keep awake mode was not running.")

def _create_awake_script():
    # Make sure directory exists
    os.makedirs(os.path.dirname(SCRIPT_PATH), exist_ok=True)
    
    content = """
import pyautogui
import time
import sys

# Move mouse 1 pixel every 60 seconds to prevent sleep
try:
    while True:
        pyautogui.moveRel(1, 0)
        pyautogui.moveRel(-1, 0)
        time.sleep(60)
except KeyboardInterrupt:
    sys.exit()
"""
    with open(SCRIPT_PATH, 'w') as f:
        f.write(content.strip())
