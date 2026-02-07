import platform
from components.system.custom_utils import run_in_separate_terminal

def check_login_history(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Checking login history.", blocking=False)
        
    if os_type == 'Linux' or os_type == 'Darwin':
            run_in_separate_terminal('last', "LOGIN HISTORY", os_type, speaker)
    elif os_type == 'Windows':
            run_in_separate_terminal('query user', "LOGIN HISTORY", os_type, speaker)
