import os
import subprocess
import platform
import shutil

# Only import winreg on Windows
if platform.system() == "Windows":
    import winreg

def get_platform():
    if platform.system() == "Windows":
        return "windows"
    elif platform.system() == "Darwin":
        return "macos"
    else:
        return "linux"

def get_app_path_from_registry(app_name):
    """
    Attempts to find the application path from the Windows Registry.
    Searches in HKLM and HKCU under Software\Microsoft\Windows\CurrentVersion\App Paths
    """
    if get_platform() != "windows":
        return None

    search_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
    ]

    possible_names = [app_name, app_name + ".exe"]

    for hkey, param_path in search_paths:
        for name in possible_names:
            try:
                # Open the key for the specific app
                key_handle = winreg.OpenKey(hkey, f"{param_path}\\{name}")
                # Get the default value (path to executable)
                path, _ = winreg.QueryValueEx(key_handle, "")
                winreg.CloseKey(key_handle)
                if path and os.path.exists(path):
                    return path
            except OSError:
                continue
    return None

def is_app_installed(app_name):
    """
    Checks if an application is installed/available in the system path, registry, or if it's a local file.
    """
    plat = get_platform()
    
    # 1. Check if it's a local file first
    if os.path.exists(app_name):
        return True

    if plat == "linux":
        # Check standard bin paths using 'which'
        if shutil.which(app_name):
            return True
        return False
        
    elif plat == "macos":
        try:
            subprocess.check_output(["open", "-Ra", app_name], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            return False
            
    elif plat == "windows":
        # 1. Check PATH using shutil.which (covers .exe, .bat, etc in PATH)
        if shutil.which(app_name):
            return True
            
        # 2. Check Registry (App Paths)
        if get_app_path_from_registry(app_name):
            return True
            
        # 3. Last resort fallback to 'where' (sometimes finds things shutil.which misses if configured oddly)
        try:
            subprocess.check_output(f"where {app_name}", stderr=subprocess.STDOUT, shell=True)
            return True
        except subprocess.CalledProcessError:
            return False
            
    return False

from components.application.app_mapper import AppMapper

# Global instance to avoid reloading every time (though caching would be better)
# For now, we instantiate on import or first use? 
# Better to instantiate inside function to avoid startup cost if not needed, 
# or use a singleton pattern.
_mapper = None

def get_mapper():
    global _mapper
    if _mapper is None:
        _mapper = AppMapper()
    return _mapper

def open_application(app_name, speaker):
    """
    Opens the specified application or file.
    """
    app_name = app_name.strip()
    
    # Pre-processing common names
    bin_mapping = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "code": "code", # code is usually in PATH
        "vscode": "code",
        "calculator": "calc.exe",
        "notepad": "notepad.exe",
        "command prompt": "cmd.exe",
        "terminal": "cmd.exe", # Default windows terminal
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "files": "explorer.exe",
        "edge": "msedge.exe",
        "microsoft edge": "msedge.exe",
        "paint": "mspaint.exe",
        "settings": "ms-settings:", 
    }

    # 1. Check heuristics/hardcoded map first
    target_app = bin_mapping.get(app_name.lower(), app_name)
    
    # 2. If not found in simple map, or if simple map result isn't installed...
    # Actually, we should check AppMapper if simple logic fails or if it's not a path/exe.
    
    plat = get_platform()
    mapper_result = None
    
    # If it's a known mapping like "chrome.exe", we might still want to check AppMapper 
    # if standard detection fails, but usually "chrome.exe" is fine.
    # The real value of AppMapper is for "whatsapp", "spotify".
    
    if target_app == app_name and " " not in app_name and "." not in app_name:
         # Likely a simple name like "whatsapp" that user said
         pass

    # Try to find in AppMapper if it's not a clear executable
    mapper = get_mapper()
    mapped_cmd = mapper.search_app(app_name)
    
    if mapped_cmd:
        print(f"[Application] AppMapper found: {app_name} -> {mapped_cmd}")
        # Use the mapped command
        target_app = mapped_cmd
    
    # Platform specific adjustments
    if plat == "linux":
        # Linux specific re-mapping if needed
        if target_app == "code": target_app = "code" 
        if target_app == "calculator": target_app = "gnome-calculator"
    
    print(f"[Application] Request to open: {app_name} (Target: {target_app})")

    # Check existence
    # Logic update: if target_app starts with shell:, it's valid for Windows
    is_shell_cmd = target_app.lower().startswith("shell:")
    
    if not is_shell_cmd and not is_app_installed(target_app) and not target_app.startswith("ms-settings:"): 
        speaker.speak(f"I cannot find {app_name} on your system.")
        return

    try:
        if plat == "linux":
            subprocess.Popen(f"nohup {target_app} >/dev/null 2>&1 &", shell=True)
            speaker.speak(f"Opening {app_name}")
            
        elif plat == "macos":
            subprocess.Popen(["open", "-a", target_app])
            speaker.speak(f"Opening {app_name}")
            
        elif plat == "windows":
            # If it's a shell command (UWP), use start
            if is_shell_cmd:
                 os.system(f"start \"\" \"{target_app}\"")
                 speaker.speak(f"Opening {app_name}")
                 return

            # If it's a local file or registry path, os.startfile is best
            # Use registry path if available
            reg_path = get_app_path_from_registry(target_app)
            
            if reg_path:
                 os.startfile(reg_path)
            else:
                try:
                    os.startfile(target_app)
                except OSError:
                     os.system(f"start {target_app}")
                     
            speaker.speak(f"Opening {app_name}")
            
    except Exception as e:
        print(f"[Error] Failed to open {app_name}: {e}")
        speaker.speak(f"I encountered an error trying to open {app_name}.")
