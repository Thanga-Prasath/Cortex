import platform
import os
import shutil
import subprocess

if platform.system() == "Windows":
    import winreg

def get_default_browser():
    """
    Finds the default browser executable path or name.
    Works on Windows, Linux, and macOS.
    """
    os_type = platform.system()
    
    if os_type == "Linux":
        # Use xdg-settings to get the actual default browser .desktop file
        try:
            result = subprocess.run(
                ["xdg-settings", "get", "default-web-browser"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                desktop_file = result.stdout.strip()  # e.g., "firefox.desktop"
                # Try to extract the executable from the .desktop file
                browser_path = _resolve_desktop_file(desktop_file)
                if browser_path:
                    return browser_path
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback: check common browsers
        browsers = find_installed_browsers()
        if browsers:
            return browsers[0]['path']
        return "xdg-open"  # Last resort
    
    elif os_type == "Darwin":
        # macOS: Get default browser via LaunchServices
        try:
            # Get the bundle ID of the default browser
            result = subprocess.run(
                ["defaults", "read", "com.apple.LaunchServices/com.apple.launchservices.secure",
                 "LSHandlers"],
                capture_output=True, text=True, timeout=5
            )
            # Parse for HTTP handler - this is complex, so fallback to common approach
        except Exception:
            pass
        
        # Simpler approach: check common macOS browsers
        mac_browsers = [
            ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "Google Chrome"),
            ("/Applications/Firefox.app/Contents/MacOS/firefox", "Firefox"),
            ("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge", "Edge"),
            ("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser", "Brave"),
            ("/Applications/Safari.app/Contents/MacOS/Safari", "Safari"),
        ]
        for path, name in mac_browsers:
            if os.path.exists(path):
                return path
        return "open"  # macOS default opener
    
    elif os_type == "Windows":
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


def _resolve_desktop_file(desktop_filename):
    """
    Given a .desktop filename (e.g. 'firefox.desktop'), find the Exec= line
    and return the executable path.
    """
    # Search common .desktop file locations
    search_dirs = [
        "/usr/share/applications",
        "/usr/local/share/applications",
        os.path.expanduser("~/.local/share/applications"),
        "/var/lib/flatpak/exports/share/applications",
        os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
    ]
    
    for search_dir in search_dirs:
        filepath = os.path.join(search_dir, desktop_filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('Exec='):
                            # Extract the command (remove field codes like %u, %U, %f etc.)
                            exec_line = line[5:].strip()
                            # Remove common field codes
                            for code in ['%u', '%U', '%f', '%F', '%i', '%c', '%k']:
                                exec_line = exec_line.replace(code, '')
                            exec_cmd = exec_line.strip().split()[0] if exec_line.strip() else None
                            if exec_cmd:
                                # Resolve to full path if needed
                                full_path = shutil.which(exec_cmd)
                                return full_path if full_path else exec_cmd
            except (IOError, IndexError):
                continue
    
    # If the desktop filename hints at the browser name, try direct lookup
    browser_name = desktop_filename.replace('.desktop', '')
    path = shutil.which(browser_name)
    if path:
        return path
    
    return None

def find_installed_browsers():
    """
    Scans the system for common browsers and returns a list of dictionaries.
    """
    found = []
    os_type = platform.system()
    
    if os_type == "Windows":
        # Common browsers and their expected binary names/paths on Windows
        browser_defs = [
            {"name": "Google Chrome", "exec": "chrome.exe", "icon": "🌐"},
            {"name": "Microsoft Edge", "exec": "msedge.exe", "icon": "🌐"},
            {"name": "Mozilla Firefox", "exec": "firefox.exe", "icon": "🦊"},
            {"name": "Brave", "exec": "brave.exe", "icon": "🦁"},
            {"name": "Opera", "exec": "opera.exe", "icon": "Ｏ"}
        ]
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
    
    elif os_type == "Linux":
        # Linux browsers with all common binary name variants
        linux_browsers = [
            {"name": "Google Chrome", "execs": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"], "icon": "🌐"},
            {"name": "Mozilla Firefox", "execs": ["firefox", "firefox-esr"], "icon": "🦊"},
            {"name": "Microsoft Edge", "execs": ["microsoft-edge", "microsoft-edge-stable"], "icon": "🌐"},
            {"name": "Brave", "execs": ["brave", "brave-browser", "brave-browser-stable"], "icon": "🦁"},
            {"name": "Opera", "execs": ["opera"], "icon": "Ｏ"},
            {"name": "Vivaldi", "execs": ["vivaldi", "vivaldi-stable"], "icon": "🌐"},
            {"name": "Epiphany", "execs": ["epiphany", "epiphany-browser", "gnome-web"], "icon": "🌐"},
        ]
        for b in linux_browsers:
            for exe in b['execs']:
                path = shutil.which(exe)
                if path:
                    found.append({"name": b['name'], "path": path, "icon": b['icon']})
                    break  # Found one variant, skip others
    
    elif os_type == "Darwin":
        # macOS browsers in .app bundles
        mac_browsers = [
            {"name": "Google Chrome", "app": "/Applications/Google Chrome.app", "icon": "🌐"},
            {"name": "Mozilla Firefox", "app": "/Applications/Firefox.app", "icon": "🦊"},
            {"name": "Microsoft Edge", "app": "/Applications/Microsoft Edge.app", "icon": "🌐"},
            {"name": "Brave", "app": "/Applications/Brave Browser.app", "icon": "🦁"},
            {"name": "Safari", "app": "/Applications/Safari.app", "icon": "🧭"},
            {"name": "Opera", "app": "/Applications/Opera.app", "icon": "Ｏ"},
        ]
        for b in mac_browsers:
            if os.path.exists(b['app']):
                found.append({"name": b['name'], "path": b['app'], "icon": b['icon']})
                
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
