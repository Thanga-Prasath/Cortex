import platform
from components.system.custom_utils import run_in_separate_terminal

def get_ip_address(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Checking IP address.", blocking=False)
        
    if os_type == 'Windows':
        run_in_separate_terminal('ipconfig', "IP ADDRESS", os_type, speaker)
    else:
        run_in_separate_terminal('hostname -I', "IP ADDRESS", os_type, speaker)
