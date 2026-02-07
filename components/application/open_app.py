import os
import subprocess
import platform
import shutil

def get_platform():
    if platform.system() == "Windows":
        return "windows"
    elif platform.system() == "Darwin":
        return "macos"
    else:
        return "linux"

def is_app_installed(app_name):
    """
    Checks if an application is installed/available in the system path.
    """
    plat = get_platform()
    
    if plat == "linux":
        # Check standard bin paths using 'which'
        if shutil.which(app_name):
            return True
        # Try checking strict snap/flatpak if needed, but shutil.which covers /usr/bin, /bin, etc.
        return False
        
    elif plat == "macos":
        # macOS apps are often in /Applications. 'mdfind' is powerful but slow.
        # open -Ra returns path if app exists
        try:
            # -R reveals app in finder, if it returns 0 it exists
            subprocess.check_output(["open", "-Ra", app_name], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            return False
            
    elif plat == "windows":
        # Check using 'where' command
        try:
            subprocess.check_output(["where", app_name], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            # Fallback: Common paths check could be added, or assume False
            return False
            
    return False

def open_application(app_name, speaker):
    """
    Opens the specified application.
    """
    app_name = app_name.strip()
    
    # Pre-processing common names if needed (e.g. "code" -> "code", "chrome" -> "google-chrome")
    # Mapping friendly names to binary names
    bin_mapping = {
        "chrome": "google-chrome",
        "google chrome": "google-chrome",
        "firefox": "firefox",
        "code": "code",
        "vscode": "code",
        "calculator": "gnome-calculator", # Linux specific often
        "terminal": "gnome-terminal"
    }

    # If it's a known alias, verify the binary alias first
    target_app = bin_mapping.get(app_name.lower(), app_name)
    
    print(f"[Application] Request to open: {app_name} (Target: {target_app})")

    if not is_app_installed(target_app):
        # Specific check for generic names on Linux if the specific binary wasn't found
        # e.g. "calculator" might be 'kcalc' or 'galculator'
        speaker.speak(f"I cannot find {app_name} on your system. Please make sure it is installed.")
        return

    plat = get_platform()
    
    try:
        if plat == "linux":
            # nohup to detach, & to background
            subprocess.Popen(f"nohup {target_app} >/dev/null 2>&1 &", shell=True)
            speaker.speak(f"Opening {app_name}")
            
        elif plat == "macos":
            subprocess.Popen(["open", "-a", target_app])
            speaker.speak(f"Opening {app_name}")
            
        elif plat == "windows":
            os.system(f"start {target_app}")
            speaker.speak(f"Opening {app_name}")
            
    except Exception as e:
        print(f"[Error] Failed to open {app_name}: {e}")
        speaker.speak(f"I encountered an error trying to open {app_name}.")
