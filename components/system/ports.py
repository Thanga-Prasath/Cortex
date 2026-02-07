import platform
from components.system.custom_utils import run_in_separate_terminal

def check_ports(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Checking open network ports.", blocking=False)
        
    if os_type == 'Linux':
        run_in_separate_terminal('sudo ss -tulnp', "OPEN PORTS", os_type, speaker)
    else:
            run_in_separate_terminal('netstat -an', "OPEN PORTS", os_type, speaker)
