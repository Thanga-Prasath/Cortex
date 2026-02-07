import platform
import os
from components.system.custom_utils import run_in_separate_terminal

def clear_dns_cache(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Clearing DNS cache.", blocking=False)
    
    if os_type == 'Linux':
        # Ubuntu/Systemd
        cmd = "sudo resolvectl flush-caches"
        run_in_separate_terminal(cmd, "CLEAR DNS", os_type, speaker)
    elif os_type == 'Windows':
        cmd = "ipconfig /flushdns"
        run_in_separate_terminal(cmd, "CLEAR DNS", os_type, speaker)
    elif os_type == 'Darwin':
        cmd = "sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"
        run_in_separate_terminal(cmd, "CLEAR DNS", os_type, speaker)
