import platform
from components.system.custom_utils import run_in_separate_terminal

def check_connections(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Listing active network connections.", blocking=False)
        
    if os_type == 'Linux':
            run_in_separate_terminal('sudo ss -putan', "NETWORK CONNECTIONS", os_type, speaker)
    elif os_type == 'Windows':
            run_in_separate_terminal('netstat -ano', "NETWORK CONNECTIONS", os_type, speaker)
    elif os_type == 'Darwin':
            run_in_separate_terminal('netstat -an', "NETWORK CONNECTIONS", os_type, speaker)
