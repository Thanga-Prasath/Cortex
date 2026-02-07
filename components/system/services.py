import platform
from components.system.custom_utils import run_in_separate_terminal

def manage_system_services(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Creating list of system services.", blocking=False)
    
    if os_type == 'Linux':
        cmd = "systemctl list-units --type=service"
        run_in_separate_terminal(cmd, "SYSTEM SERVICES", os_type, speaker)
    elif os_type == 'Windows':
        cmd = "net start" # or sc query
        run_in_separate_terminal(cmd, "SYSTEM SERVICES", os_type, speaker)
    elif os_type == 'Darwin':
        cmd = "launchctl list"
        run_in_separate_terminal(cmd, "SYSTEM SERVICES", os_type, speaker)
