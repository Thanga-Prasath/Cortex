import platform
from components.system.custom_utils import run_in_separate_terminal

def list_installed_apps(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Listing installed applications.", blocking=False)
    
    if os_type == 'Linux':
        # listing /usr/bin or snap or dpkg
        # apt list --installed is good but long
        cmd = "apt list --installed"
        run_in_separate_terminal(cmd, "INSTALLED APPS", os_type, speaker)
    elif os_type == 'Windows':
        # Get-AppxPackage is decent, or list from registry
        cmd = "powershell -Command \"Get-StartApps\""
        run_in_separate_terminal(cmd, "INSTALLED APPS", os_type, speaker)
    elif os_type == 'Darwin':
        cmd = "ls /Applications"
        run_in_separate_terminal(cmd, "INSTALLED APPS", os_type, speaker)
