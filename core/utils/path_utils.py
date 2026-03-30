import os
import sys
import platform

def get_base_path() -> str:
    """
    Get the absolute path to the base directory of the application.
    This works reliably both when running as a normal Python script
    and when packaged as an executable (e.g. PyInstaller or Nuitka).
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # For a onefile build, this is a temp folder.
        # For a folder build, this is the root folder containing the .exe
        return sys._MEIPASS
    elif sys.argv and sys.argv[0].endswith('.exe'):
        # Fallback for Nuitka standalone directory builds
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # Running as a normal Python script
        # Go up two directory levels from core/utils/path_utils.py -> core -> base
        current_dir = os.path.dirname(os.path.abspath(__file__))
        core_dir = os.path.dirname(current_dir)
        base_dir = os.path.dirname(core_dir)
        return base_dir

def get_data_path() -> str:
    """
    Get the absolute path to the data directory.
    This ensures templates, configs, and models are always found.
    """
    return os.path.join(get_base_path(), 'data')

def get_user_data_path() -> str:
    """
    Get the path to a writable user data directory.
    Crucial for packaged Windows apps that install to Program Files (read-only).
    On Windows: %LOCALAPPDATA%/Cortex
    On Linux: ~/.local/share/Cortex
    """
    if platform.system() == 'Windows':
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
    elif platform.system() == 'Darwin':
        base = os.path.expanduser('~/Library/Application Support')
    else:
        base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
        
    app_dir = os.path.join(base, 'Cortex')
    os.makedirs(app_dir, exist_ok=True)
    return app_dir
