# PyInstaller runtime hook for ctranslate2
# Runs BEFORE any Python module is imported in the frozen exe.
#
# Problem: ctranslate2's __init__.py calls:
#   os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)))
# …to tell Windows where ctranslate2.dll / libiomp5md.dll live.
# But when PyInstaller collects these DLLs, they land in _MEIPASS/ctranslate2/
# (as data-files) AFTER the DLL loader has already tried and failed to find them.
# PyInstaller's early DLL resolution uses a different search path.
#
# Fix: Pre-register the ctranslate2 subfolder with os.add_dll_directory()
# so the Windows DLL loader finds ctranslate2.dll and libiomp5md.dll
# before the C extension tries to reference them.

import os
import sys

if hasattr(sys, '_MEIPASS'):
    _ct2_dir = os.path.join(sys._MEIPASS, 'ctranslate2')
    
    # 1. Register for Python's import system
    os.add_dll_directory(sys._MEIPASS)
    if os.path.isdir(_ct2_dir):
        os.add_dll_directory(_ct2_dir)
    
    # 2. Register for C++ internal LoadLibrary calls (CRITICAL for Windows)
    # Windows native LoadLibrary ignores os.add_dll_directory and only checks PATH.
    new_path = sys._MEIPASS
    if os.path.isdir(_ct2_dir):
        new_path = new_path + os.pathsep + _ct2_dir
        
    current_path = os.environ.get("PATH", "")
    os.environ["PATH"] = new_path + os.pathsep + current_path

