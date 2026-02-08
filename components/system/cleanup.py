import platform
import os
from components.system.custom_utils import run_in_separate_terminal

def clean_system(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Starting system cleanup.", blocking=False)
        
    if os_type == 'Linux':
            # Safe cleanup: apt clean, autoremove (unused deps), and user thumbnail cache
            # Adding -y for non-interactive
            cmd = (
                "echo 'Cleaning package cache...'; sudo apt-get clean; "
                "echo 'Removing unused dependencies...'; sudo apt-get autoremove -y; "
                "echo 'Clearing thumbnail cache...'; rm -rf ~/.cache/thumbnails/*; "
                "echo 'Cleanup Complete!'"
            )
            run_in_separate_terminal(cmd, "SYSTEM CLEANUP", os_type, speaker)
            
    elif os_type == 'Windows':
            # Clean %TEMP% folder safely
            # Removed 'msg' command as it's not available on all editions (e.g. Home)
            # /q = quiet, /f = force, /s = subdirectories
            cmd = 'echo Cleaning temporary files... & del /q /f /s %TEMP%\\* & echo. & echo Cleanup Complete!'
            run_in_separate_terminal(cmd, "SYSTEM CLEANUP", os_type, speaker, admin=True)
            
    elif os_type == 'Darwin': # MacOS
            # Clear User Caches and brew cleanup if available
            cmd = (
                "echo 'Cleaning User Caches...'; rm -rf ~/Library/Caches/*; "
                "if command -v brew &> /dev/null; then echo 'Running Homebrew Cleanup...'; brew cleanup; fi; "
                "echo 'Cleanup Complete!'"
            )
            run_in_separate_terminal(cmd, "SYSTEM CLEANUP", os_type, speaker)
