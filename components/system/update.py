import platform
from components.system.custom_utils import run_in_separate_terminal

def check_for_updates(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Checking for system updates.", blocking=False)
    
    if os_type == 'Linux':
        # Assuming apt for Debian/Ubuntu based systems
        cmd = "sudo apt update && apt list --upgradable"
        run_in_separate_terminal(cmd, "SYSTEM UPDATES", os_type, speaker)
    elif os_type == 'Windows':
        # Requires PowerShell module PSWindowsUpdate usually, but we can try generic
        # or just open Windows Update settings?
        # A command to strictly list updates via PS without extra modules is tricky/slow.
        # Fallback to opening settings URI for reliability?
        # But user asked for function, so let's try USOClient (undocumented but works) or just start ms-settings:windowsupdate
        # Let's try to run a command that shows info if possible, referencing plan: "PowerShell Get-WindowsUpdate"
        # Since Get-WindowsUpdate needs a module, we might stick to a simpler check or informing user.
        # Let's try to open the update settings as a fallback for visual check.
        cmd = "start ms-settings:windowsupdate"
        # But we need output in terminal?
        # Let's try:
        cmd_show = "echo 'Opening Windows Update Settings...' & start ms-settings:windowsupdate"
        run_in_separate_terminal(cmd_show, "SYSTEM UPDATES", os_type, speaker)
    elif os_type == 'Darwin':
        cmd = "softwareupdate -l"
        run_in_separate_terminal(cmd, "SYSTEM UPDATES", os_type, speaker)
