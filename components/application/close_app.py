import os
import subprocess
import platform

def get_platform():
    if platform.system() == "Windows":
        return "windows"
    elif platform.system() == "Darwin":
        return "macos"
    else:
        return "linux"

def close_application(app_name, speaker):
    """
    Closes the specified application.
    """
    app_name = app_name.strip()
    plat = get_platform()
    
    # Simple mapping for better hit rate
    bin_mapping = {
        "chrome": "google-chrome",
        "google chrome": "google-chrome",
        "firefox": "firefox",
        "code": "code",
        "vscode": "code"
    }
    
    target_app = bin_mapping.get(app_name.lower(), app_name)
    
    print(f"[Application] Request to close: {app_name} (Target: {target_app})")

    try:
        if plat == "linux":
            # pkill is generally available
            subprocess.run(["pkill", "-f", target_app])
            speaker.speak(f"Closing {app_name}")
            
        elif plat == "macos":
            # AppleScript is cleanest for graceful exit
            script = f'quit app "{target_app}"'
            subprocess.run(["osascript", "-e", script])
            speaker.speak(f"Closing {app_name}")
            
        elif plat == "windows":
            # taskkill /IM appname.exe /F
            # We might need to guess the extension or use image name
            subprocess.run(f"taskkill /IM {target_app}.exe /F", shell=True)
            speaker.speak(f"Closing {app_name}")
            
    except Exception as e:
        print(f"[Error] Failed to close {app_name}: {e}")
        speaker.speak(f"I encountered an issue closing {app_name}.")
