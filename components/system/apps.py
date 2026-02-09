import platform
import subprocess
import sys
from components.system.custom_utils import run_in_separate_terminal

def list_installed_apps(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Opening Installed Applications Manager.", blocking=False)
    
    if os_type == 'Linux':
        # listing /usr/bin or snap or dpkg
        # apt list --installed is good but long
        cmd = "apt list --installed"
        run_in_separate_terminal(cmd, "INSTALLED APPS", os_type, speaker)
    elif os_type == 'Windows':
        try:
            # Launch the GUI as a separate process
            subprocess.Popen([sys.executable, "-m", "core.ui.apps_window"])
        except Exception as e:
            if speaker:
                speaker.speak(f"Failed to open applications manager: {e}")
            print(f"Error launching apps window: {e}")
    elif os_type == 'Darwin':
        cmd = "ls /Applications"
        run_in_separate_terminal(cmd, "INSTALLED APPS", os_type, speaker)
