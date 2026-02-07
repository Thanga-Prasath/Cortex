import platform
from components.system.custom_utils import run_in_separate_terminal

def list_files(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Listing files in current directory.", blocking=False)
        
    if os_type == 'Windows':
        run_in_separate_terminal('dir', "CURRENT DIRECTORY", os_type, speaker)
    else:
        run_in_separate_terminal('ls -la', "CURRENT DIRECTORY", os_type, speaker)
