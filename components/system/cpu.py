import platform
import os
from components.system.custom_utils import run_in_separate_terminal

def get_cpu_info(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Retrieving CPU information.", blocking=False)
    
    if os_type == 'Linux':
        cmd = "lscpu"
        run_in_separate_terminal(cmd, "CPU INFO", os_type, speaker)
    elif os_type == 'Windows':
        cmd = "wmic cpu get caption, deviceid, name, numberofcores, maxclockspeed, status"
        run_in_separate_terminal(cmd, "CPU INFO", os_type, speaker)
    elif os_type == 'Darwin':
        cmd = "sysctl -a | grep machdep.cpu"
        run_in_separate_terminal(cmd, "CPU INFO", os_type, speaker)
