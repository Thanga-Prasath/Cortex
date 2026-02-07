import platform
import os
from components.system.custom_utils import run_in_separate_terminal

def get_current_user(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Identifying current user.", blocking=False)
    
    # Python generic way
    try:
        user = os.getlogin()
    except:
        import getpass
        user = getpass.getuser()
        
    cmd = f"echo Current User: {user}; id"
    run_in_separate_terminal(cmd, "CURRENT USER", os_type, speaker)
