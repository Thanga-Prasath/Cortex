import platform
from components.system.custom_utils import run_in_separate_terminal

def check_disk(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Checking disk storage.", blocking=False)
        
    if os_type == 'Windows':
         run_in_separate_terminal('wmic logicaldisk get size,freespace,caption', "DISK STORAGE", os_type, speaker)
    else:
         run_in_separate_terminal('df -h .', "DISK STORAGE", os_type, speaker)
