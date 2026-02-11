import platform
import subprocess
import os
import sys

def _run_command(cmd):
    if platform.system() == 'Windows':
        subprocess.run(cmd, shell=True)
    else:
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def lock_screen(speaker):
    speaker.speak("Locking the screen.")
    os_type = platform.system()
    if os_type == 'Windows':
        _run_command("rundll32.exe user32.dll,LockWorkStation")
    elif os_type == 'Darwin':
        _run_command("pmset displaysleepnow")
    elif os_type == 'Linux':
        # Gnome specific, might need checks for other DEs
        _run_command("gnome-screensaver-command -l")

def sleep_system(speaker):
    speaker.speak("Putting system to sleep.")
    os_type = platform.system()
    if os_type == 'Windows':
        # Hibernate off might be needed for S3 sleep, but this is standard command
        _run_command("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif os_type == 'Darwin':
        _run_command("pmset sleepnow")
    elif os_type == 'Linux':
        _run_command("systemctl suspend")

def _confirm_action(action_name, speaker, listener):
    speaker.speak(f"Are you sure you want to {action_name}? Please say yes or no.")
    response = listener.listen(timeout=5)
    
    if response:
        response = response.lower()
        if "yes" in response or "sure" in response or "confirm" in response:
            return True
    
    speaker.speak(f"{action_name.capitalize()} cancelled.")
    return False

def restart_system(speaker, listener):
    if _confirm_action("restart the system", speaker, listener):
        speaker.speak("Restarting system now.")
        os_type = platform.system()
        if os_type == 'Windows':
            _run_command("shutdown /r /t 0")
        elif os_type == 'Darwin':
            _run_command("shutdown -r now")
        elif os_type == 'Linux':
            _run_command("systemctl reboot")

def shutdown_system(speaker, listener):
    if _confirm_action("shutdown the system", speaker, listener):
        speaker.speak("Shutting down system. Goodbye.")
        os_type = platform.system()
        if os_type == 'Windows':
            _run_command("shutdown /s /t 0")
        elif os_type == 'Darwin':
            _run_command("shutdown -h now")
        elif os_type == 'Linux':
            _run_command("systemctl poweroff")
