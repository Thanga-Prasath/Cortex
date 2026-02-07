import platform
import os
from components.system.custom_utils import run_in_separate_terminal, get_cmd_with_auto_install

def check_network_traffic(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Checking network traffic usage.", blocking=False)
        
    if os_type == 'Linux':
        # Try iftop first (needs sudo), then nload, then fallback
        if os.system("which iftop > /dev/null 2>&1") == 0:
                run_in_separate_terminal('sudo iftop', "NETWORK TRAFFIC", os_type, speaker)
        elif os.system("which nload > /dev/null 2>&1") == 0:
                run_in_separate_terminal('nload', "NETWORK TRAFFIC", os_type, speaker)
        else:
                # Auto install iftop
                cmd = "echo 'Installing iftop...'; sudo apt install iftop -y; sudo iftop"
                run_in_separate_terminal(cmd, "NETWORK TRAFFIC (Installing...)", os_type, speaker)
                
    elif os_type == 'Windows':
            run_in_separate_terminal('netstat -e', "NETWORK TRAFFIC (Bytes)", os_type, speaker)
    elif os_type == 'Darwin':
            run_in_separate_terminal('netstat -ib', "NETWORK TRAFFIC (Stats)", os_type, speaker)
