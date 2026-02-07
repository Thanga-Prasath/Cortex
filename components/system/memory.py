import platform
from components.system.custom_utils import run_in_separate_terminal

def check_memory(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Checking memory usage.", blocking=False)
        
    if os_type == 'Linux':
        run_in_separate_terminal('free -h', "MEMORY USAGE", os_type, speaker)
    elif os_type == 'Darwin':
        run_in_separate_terminal('vm_stat', "MEMORY USAGE", os_type, speaker)
    elif os_type == 'Windows':
        run_in_separate_terminal('systeminfo', "MEMORY USAGE", os_type, speaker)
