import platform
import os
from components.system.custom_utils import run_in_separate_terminal

def system_info(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Opening system information console.", blocking=False)
    
    if os_type == 'Linux':
        # Check for neofetch or fastfetch for a pretty output
        if os.system("which fastfetch > /dev/null 2>&1") == 0:
                run_in_separate_terminal('fastfetch', "SYSTEM INFO", os_type)
        elif os.system("which neofetch > /dev/null 2>&1") == 0:
                run_in_separate_terminal('neofetch', "SYSTEM INFO", os_type)
        else:
                # Fallback to manual info
                cmd = (
                    "echo 'OS: ' $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2); "
                    "echo 'Kernel: ' $(uname -r); "
                    "echo 'Uptime: ' $(uptime -p); "
                    "echo 'Memory: ' $(free -h | grep Mem | awk '{print $3 \" / \" $2}'); "
                    "echo 'Disk: '; df -h / | tail -n 1 | awk '{print \"  \" $4 \" free / \" $2 \" total\"}'"
                )
                run_in_separate_terminal(cmd, "SYSTEM INFO", os_type)
                
    elif os_type == 'Windows':
        run_in_separate_terminal('systeminfo', "SYSTEM INFO", os_type)
        
    elif os_type == 'Darwin':
        run_in_separate_terminal('system_profiler SPSoftwareDataType SPHardwareDataType', "SYSTEM INFO", os_type)
