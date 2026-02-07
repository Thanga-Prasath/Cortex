import subprocess
import os
import platform

def get_os_type():
    return platform.system()

def get_cmd_with_auto_install(command, package):
    """Returns a shell command that tries to install the package if the command is missing (Linux only)."""
    if get_os_type() == 'Linux':
        # Check if command exists, if not, try to install
        return f"which {command} > /dev/null 2>&1 || (echo 'Tool {command} not found. Installing {package}...' && sudo apt install {package} -y); {command}"
    return command

def run_in_separate_terminal(command, title="System Info", os_type=None, speaker=None):
    """Launches a command in a new terminal window."""
    if os_type is None:
        os_type = get_os_type()

    try:
        if os_type == 'Linux':
            # Try gnome-terminal first, then x-terminal-emulator
            # We wrap the command in bash to keep the window open
            full_cmd = f"echo '{title}'; echo '===================='; {command}; echo ''; read -p 'Press Enter to close...' var"
            
            try:
                subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', full_cmd])
            except FileNotFoundError:
                # Fallback
                subprocess.Popen(['x-terminal-emulator', '-e', f"bash -c \"{full_cmd}\""])
                
        elif os_type == 'Windows':
            # start cmd /k keeps window open
            subprocess.Popen(['start', 'cmd', '/k', f"echo {title} & echo ==================== & {command}"], shell=True)
            
        elif os_type == 'Darwin': # MacOS
            # AppleScript to open Terminal
            script = f'''tell application "Terminal" to do script "{command}"'''
            subprocess.Popen(['osascript', '-e', script])
            
    except Exception as e:
        print(f"Failed to open terminal: {e}")
        if speaker:
            speaker.speak("I could not open a new terminal window.")
