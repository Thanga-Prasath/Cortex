import platform
from components.system.custom_utils import run_in_separate_terminal, get_cmd_with_auto_install

def check_processes(speaker=None):
    os_type = platform.system()
    if speaker:
         speaker.speak("Opening process monitor.", blocking=False)

    if os_type == 'Linux':
        # Auto-install htop
        cmd = get_cmd_with_auto_install('htop', 'htop')
        run_in_separate_terminal(cmd, "PROCESS MONITOR", os_type, speaker)
    elif os_type == 'Windows':
            run_in_separate_terminal('tasklist', "PROCESS MONITOR", os_type, speaker)
    elif os_type == 'Darwin':
            run_in_separate_terminal('top', "PROCESS MONITOR", os_type, speaker)
