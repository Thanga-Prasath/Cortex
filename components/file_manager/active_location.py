import os
import subprocess
import json
from pathlib import Path

def get_active_window_hyprland():
    """
    Get active window title using hyprctl (for Hyprland).
    """
    try:
        output = subprocess.check_output(['hyprctl', 'activewindow', '-j'], stderr=subprocess.DEVNULL)
        window_info = json.loads(output.decode('utf-8'))
        return window_info.get('title', None)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        pass
    return None

def get_active_window_title():
    """
    Get the active window title trying multiple methods:
    1. hyprctl (Hyprland)
    2. xprop (X11 / XWayland)
    """
    # Try Hyprland first
    title = get_active_window_hyprland()
    if title:
        return title

    # Fallback to xprop
    try:
        # 1. Get the active window ID
        root_check = subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stderr=subprocess.DEVNULL)
        # Output format: _NET_ACTIVE_WINDOW(WINDOW): window id # 0x1234567
        root_str = root_check.decode('utf-8').strip()
        
        if 'window id #' not in root_str:
            return None
        
        window_id = root_str.split('window id #')[-1].strip()
        
        # 2. Get the window name for that ID
        name_check = subprocess.check_output(['xprop', '-id', window_id, '_NET_WM_NAME'], stderr=subprocess.DEVNULL)
        # Output format: _NET_WM_NAME(UTF8_STRING) = "Title"
        name_str = name_check.decode('utf-8').strip()
        
        if '=' not in name_str:
            # Try WM_NAME as fallback
            name_check = subprocess.check_output(['xprop', '-id', window_id, 'WM_NAME'], stderr=subprocess.DEVNULL)
            name_str = name_check.decode('utf-8').strip()
        
        if '"' in name_str:
            # Extract content inside quotes
            # Using simple split might fail if title has quotes, but good enough for now
            # Usually it's at the end: ... = "Title"
            title = name_str.split('=', 1)[1].strip().strip('"')
            return title
            
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
        pass
        
    return None

def get_nautilus_path():
    """
    Query GNOME Nautilus for the current directory path via D-Bus.
    Returns Path object or None if unsuccessful.
    """
    try:
        # Get list of Nautilus windows
        result = subprocess.run(
            ['gdbus', 'call', '--session', '--dest', 'org.gnome.Nautilus',
             '--object-path', '/org/gnome/Nautilus', '--method',
             'org.freedesktop.DBus.Introspectable.Introspect'],
            capture_output=True,
            text=True,
            timeout=1
        )
        
        if result.returncode != 0:
            return None
        
        # Try to get the current location from the first window
        # Nautilus exposes windows as /org/gnome/Nautilus/window/1, /org/gnome/Nautilus/window/2, etc.
        for window_num in range(1, 10):  # Try first 10 windows
            try:
                result = subprocess.run(
                    ['gdbus', 'call', '--session', '--dest', 'org.gnome.Nautilus',
                     '--object-path', f'/org/gnome/Nautilus/window/{window_num}',
                     '--method', 'org.freedesktop.DBus.Properties.Get',
                     'org.gnome.Nautilus.Window', 'location'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    # Parse the output: (<'file:///path/to/folder'>,)
                    import re
                    match = re.search(r"file://([^'\"]+)", result.stdout)
                    if match:
                        from urllib.parse import unquote
                        path_str = unquote(match.group(1))
                        path = Path(path_str)
                        if path.exists() and path.is_dir():
                            print(f"[FileManager] Nautilus path detected: {path}")
                            return path
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                continue
                
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None

def get_dolphin_path():
    """
    Query KDE Dolphin for the current directory path via D-Bus.
    Returns Path object or None if unsuccessful.
    """
    try:
        # Try to get the current URL from Dolphin
        result = subprocess.run(
            ['qdbus', 'org.kde.dolphin', '/dolphin/Dolphin_1',
             'org.kde.dolphin.MainWindow.currentUrl'],
            capture_output=True,
            text=True,
            timeout=1
        )
        
        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip()
            if url.startswith('file://'):
                from urllib.parse import unquote
                path_str = unquote(url[7:])
                path = Path(path_str)
                if path.exists() and path.is_dir():
                    print(f"[FileManager] Dolphin path detected: {path}")
                    return path
                    
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None

def get_thunar_path():
    """
    Query XFCE Thunar for the current directory path.
    Uses window title parsing as Thunar doesn't expose D-Bus interface.
    Returns Path object or None if unsuccessful.
    """
    try:
        # Get active window title
        window_title = get_active_window_title()
        
        if not window_title or 'thunar' not in window_title.lower():
            return None
        
        # Thunar format is typically: "/path/to/folder - Thunar" or "FolderName - Thunar"
        # Try to extract the path
        import re
        
        # Pattern 1: Full path in title
        if window_title.startswith('/'):
            # Extract path before " - Thunar"
            path_match = re.match(r'^(/[^\-]+)', window_title)
            if path_match:
                path_str = path_match.group(1).strip()
                path = Path(path_str)
                if path.exists() and path.is_dir():
                    print(f"[FileManager] Thunar path detected: {path}")
                    return path
        
        # Pattern 2: Folder name in title - try common locations
        folder_match = re.match(r'^([^\-]+)\s*-\s*Thunar', window_title)
        if folder_match:
            folder_name = folder_match.group(1).strip()
            
            # Try in home directory
            home_path = Path.home() / folder_name
            if home_path.exists() and home_path.is_dir():
                print(f"[FileManager] Thunar path detected: {home_path}")
                return home_path
                
    except Exception as e:
        print(f"[FileManager] Thunar detection error: {e}")
    
    return None

def get_active_location(desktop_path=None):
    """
    Detects the current directory the user is viewing using multiple methods:
    1. Direct D-Bus queries (most reliable)
    2. Enhanced window title parsing
    3. Desktop fallback (last resort)
    """
    # Use default desktop path if not provided
    if desktop_path is None:
        desktop_path = Path.home() / "Desktop"

    # Priority 1: Try direct D-Bus queries for file managers
    print("[FileManager] Detecting active location...")
    
    # Try Nautilus
    nautilus_path = get_nautilus_path()
    if nautilus_path:
        return nautilus_path
    
    # Try Dolphin
    dolphin_path = get_dolphin_path()
    if dolphin_path:
        return dolphin_path
    
    # Try Thunar
    thunar_path = get_thunar_path()
    if thunar_path:
        return thunar_path
    
    # Priority 2: Enhanced window title parsing
    try:
        window_title = get_active_window_title()
        
        if not window_title:
            print("[FileManager] No active window detected, defaulting to Desktop")
            return desktop_path
        
        print(f"[FileManager] Active window: {window_title}")
        
        # Enhanced heuristics to extract path from title
        import re
        
        # Pattern 1: Full absolute path in title
        if window_title.startswith('/'):
            # Extract path (may have " - AppName" suffix)
            path_match = re.match(r'^(/[^\-\—]+)', window_title)
            if path_match:
                path_str = path_match.group(1).strip()
                path = Path(path_str)
                if path.exists() and path.is_dir():
                    print(f"[FileManager] Path from title (absolute): {path}")
                    return path
        
        # Pattern 2: "file:///path" format
        if 'file://' in window_title:
            match = re.search(r'file://([^\s\'"]+)', window_title)
            if match:
                from urllib.parse import unquote
                path_str = unquote(match.group(1))
                path = Path(path_str)
                if path.exists() and path.is_dir():
                    print(f"[FileManager] Path from title (file://): {path}")
                    return path
        
        # Pattern 3: Tilde expansion "~/folder"
        if '~/' in window_title:
            match = re.search(r'~/([^\s\-\—]+)', window_title)
            if match:
                path = Path.home() / match.group(1)
                if path.exists() and path.is_dir():
                    print(f"[FileManager] Path from title (tilde): {path}")
                    return path
        
        # Pattern 4: Split by common separators
        separators = [" — ", " - ", " : ", " | ", " at "]
        
        potential_names = [window_title]
        for sep in separators:
            if sep in window_title:
                potential_names.extend(window_title.split(sep))
        
        # Try each potential name
        for name in potential_names:
            name = name.strip()
            if not name or len(name) < 2:
                continue
            
            # Skip common app names
            if name.lower() in ['nautilus', 'dolphin', 'thunar', 'nemo', 'pcmanfm', 
                               'file manager', 'files', 'file browser']:
                continue
            
            # Check if it's an absolute path
            if name.startswith('/') and os.path.isdir(name):
                path = Path(name)
                print(f"[FileManager] Path from separator split (absolute): {path}")
                return path
            
            # Check if it's in Home directory
            home_path = Path.home() / name
            if home_path.is_dir():
                print(f"[FileManager] Path from separator split (home): {home_path}")
                return home_path
            
            # Check if it's in Desktop
            if desktop_path:
                desktop_subdir = desktop_path / name
                if desktop_subdir.is_dir():
                    print(f"[FileManager] Path from separator split (desktop): {desktop_subdir}")
                    return desktop_subdir
            
            # Check if it's a special name
            if name.lower() == 'home' or name == os.getlogin():
                print(f"[FileManager] Path from special name: {Path.home()}")
                return Path.home()
            
            # Check standard directories
            standard_dirs = ['Documents', 'Downloads', 'Pictures', 'Videos', 
                           'Music', 'Desktop', 'Public', 'Templates']
            if name in standard_dirs:
                std_path = Path.home() / name
                if std_path.is_dir():
                    print(f"[FileManager] Path from standard dir: {std_path}")
                    return std_path

    except Exception as e:
        print(f"[FileManager] Error in location detection: {e}")
    
    # Priority 3: Desktop fallback
    print(f"[FileManager] All detection methods failed, defaulting to Desktop: {desktop_path}")
    return desktop_path
