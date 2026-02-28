"""
Cortex Runtime Path Helper

Provides get_app_root() to resolve the application root directory correctly
in both development mode (running via python main.py) and packaged mode
(running as a PyInstaller-frozen executable).

Usage:
    from core.runtime_path import get_app_root
    config_path = os.path.join(get_app_root(), 'data', 'user_config.json')
"""

import sys
import os


def get_app_root():
    """Return the application root directory.

    - In dev mode: the current working directory (where main.py lives)
    - In PyInstaller bundle (--onedir): the directory containing the executable
    """
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        # sys.executable points to the actual executable in dist/Cortex/
        return os.path.dirname(sys.executable)
    else:
        # Running as a normal Python script
        return os.getcwd()
