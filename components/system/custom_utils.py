import subprocess
import os
import platform

def get_os_type():
    return platform.system()

def get_cmd_with_auto_install(command, package):
    """Returns a shell command that tries to install the package if the command is missing (Linux only)."""
    if get_os_type() == 'Linux':
        # Check if command exists, if not, try to install
        # We use -n (non-interactive) for sudo to avoid hanging if password is required
        return f"which {command} > /dev/null 2>&1 || (echo 'Tool {command} not found. Attempting to install {package}...' && sudo -n apt install {package} -y || echo 'Permission denied. Please run: sudo apt install {package}'); {command}"
    return command

def check_sudo_access(command):
    """Checks if a command can be run with sudo without a password prompt."""
    if get_os_type() != 'Linux':
        return True
    try:
        # sudo -n (non-interactive) returns 0 if it can run without password, 1 or other if not
        subprocess.check_call(['sudo', '-n', 'true'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def run_in_separate_terminal(command, title="System Info", os_type=None, speaker=None, admin=False):
    """Launches a command in a new terminal window."""
    if os_type is None:
        os_type = get_os_type()

    try:
        if os_type == 'Linux':
            # Try gnome-terminal first, then x-terminal-emulator
            # We wrap the command in bash to keep the window open
            try:
                # If command requires sudo, check if we have it
                if 'sudo' in command and not check_sudo_access(command):
                    full_cmd = f"echo '⚠️  AUTHENTICATION REQUIRED'; echo '===================='; echo 'The command \"{command}\" requires root privileges.'; echo 'If you have not run scripts/sunday-permissions.sh, you will be prompted for a password.'; echo ''; {command}; echo ''; read -p 'Press Enter to close...' var"
                else:
                    full_cmd = f"echo '{title}'; echo '===================='; {command}; echo ''; read -p 'Press Enter to close...' var"
                
                subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', full_cmd])
            except FileNotFoundError:
                # Fallback
                subprocess.Popen(['x-terminal-emulator', '-e', f"bash -c \"{full_cmd}\""])
                
        elif os_type == 'Windows':
            # Create a temporary batch file to mitigate quoting hell
            batch_file = os.path.join(os.getcwd(), "temp_cmd.bat")
            with open(batch_file, "w") as f:
                f.write("@echo off\n")
                f.write(f"title {title}\n")
                f.write(f"echo {title}\n")
                f.write("echo ====================\n")
                f.write(f"{command}\n")
                f.write("echo.\n")
                f.write("pause\n")
                f.write(f"del \"{batch_file}\" & exit\n") # Self-delete
            
            if admin:
                # Use PowerShell to run the batch file as Administrator
                subprocess.Popen(["powershell", "-Command", f"Start-Process cmd -ArgumentList '/c {batch_file}' -Verb RunAs"], shell=True)
            else:
                subprocess.Popen(['start', 'cmd', '/c', batch_file], shell=True)
            
        elif os_type == 'Darwin': # MacOS
            # AppleScript to open Terminal
            script = f'''tell application "Terminal" to do script "{command}"'''
            subprocess.Popen(['osascript', '-e', script])
            
    except Exception as e:
        print(f"Failed to open terminal: {e}")
        if speaker:
            speaker.speak("I could not open a new terminal window.")
