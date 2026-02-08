import platform
from components.system.custom_utils import run_in_separate_terminal

def check_firewall(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Checking firewall status.", blocking=False)
        
    if os_type == 'Linux':
        run_in_separate_terminal('sudo ufw status verbose', "FIREWALL STATUS", os_type, speaker)
    elif os_type == 'Windows':
            run_in_separate_terminal('netsh advfirewall show allprofiles', "FIREWALL STATUS", os_type, speaker, admin=True)
