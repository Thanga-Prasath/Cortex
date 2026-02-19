import platform
import os
import shutil

if platform.system() == "Windows":
    import winreg

def get_default_browser():
    """
    Finds the default browser executable path or name on Windows.
    """
    if platform.system() != "Windows":
        return "xdg-open" # Standard for Linux
    
    try:
        # Check standard HTTP association root
        reg_path = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            prog_id, _ = winreg.QueryValueEx(key, "ProgId")
        
        # Now find the command for this ProgId
        command_path = rf"{prog_id}\shell\open\command"
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
            full_cmd, _ = winreg.QueryValueEx(key, "")
            
        # Parse the command (usually "path/to/exe" %1)
        if full_cmd.startswith('"'):
            return full_cmd.split('"')[1]
        else:
            return full_cmd.split()[0]
    except Exception:
        # Fallback to checking common browsers in order of preference
        browsers = find_installed_browsers()
        if browsers:
            return browsers[0]['path']
    return None

def find_installed_browsers():
    """
    Scans the system for common browsers and returns a list of dictionaries.
    """
    found = []
    
    # Common browsers and their expected binary names/paths on Windows
    # (Simplified for now, could be expanded with registry scanning)
    browser_defs = [
        {"name": "Google Chrome", "exec": "chrome.exe", "icon": "🌐"},
        {"name": "Microsoft Edge", "exec": "msedge.exe", "icon": "🌐"},
        {"name": "Mozilla Firefox", "exec": "firefox.exe", "icon": "🦊"},
        {"name": "Brave", "exec": "brave.exe", "icon": "🦁"},
        {"name": "Opera", "exec": "opera.exe", "icon": "Ｏ"}
    ]
    
    if platform.system() == "Windows":
        for b in browser_defs:
            path = shutil.which(b['exec'])
            if not path:
                # Check Registry App Paths if not in PATH
                path = _get_app_path_from_registry(b['exec'])
                
            if path:
                found.append({
                    "name": b['name'],
                    "path": path,
                    "icon": b['icon']
                })
    else:
        # Linux/macOS simplified
        common = ["google-chrome", "firefox", "microsoft-edge", "opera", "brave"]
        for b in common:
            path = shutil.which(b)
            if path:
                found.append({"name": b.capitalize(), "path": path, "icon": "🌐"})
                
    return found

def _get_app_path_from_registry(app_name):
    """Internal helper for registry lookups."""
    try:
        search_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        ]
        for hkey, param_path in search_paths:
            try:
                key_handle = winreg.OpenKey(hkey, f"{param_path}\\{app_name}")
                path, _ = winreg.QueryValueEx(key_handle, "")
                winreg.CloseKey(key_handle)
                if path and os.path.exists(path):
                    return path
            except OSError:
                continue
    except:
        pass
    return None
