import subprocess
import platform
import os
import shutil

def _run_command(cmd, speaker):
    try:
        if platform.system() == 'Windows':
            subprocess.Popen(cmd, shell=True)
        else:
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        speaker.speak("Opening requested tool.")
    except Exception as e:
        speaker.speak(f"Failed to open tool: {e}")

def open_task_manager(speaker):
    os_type = platform.system()
    if os_type == 'Windows':
        _run_command("start taskmgr", speaker)
    elif os_type == 'Darwin':
        _run_command("open -a 'Activity Monitor'", speaker)
    elif os_type == 'Linux':
        _run_command("gnome-system-monitor", speaker)

def open_control_panel(speaker):
    os_type = platform.system()
    if os_type == 'Windows':
        # Opens traditional Control Panel. For Settings use "start ms-settings:"
        _run_command("start control", speaker) 
    elif os_type == 'Darwin':
        _run_command("open -a 'System Settings'", speaker) or _run_command("open -a 'System Preferences'", speaker)
    elif os_type == 'Linux':
        _run_command("gnome-control-center", speaker)

def open_terminal(speaker):
    os_type = platform.system()
    if os_type == 'Windows':
        # Try Windows Terminal first, then Command Prompt
        if shutil.which("wt"):
            _run_command("start wt", speaker)
        else:
            _run_command("start cmd", speaker)
    elif os_type == 'Darwin':
        _run_command("open -a Terminal", speaker)
    elif os_type == 'Linux':
        _run_command("gnome-terminal", speaker)

def open_system_config(speaker):
    """
    Opens msconfig on Windows.
    On others, opens System Information / Profiler.
    """
    os_type = platform.system()
    if os_type == 'Windows':
        _run_command("start msconfig", speaker)
    elif os_type == 'Darwin':
        _run_command(r"open /Applications/Utilities/System\ Information.app", speaker)
    elif os_type == 'Linux':
        # usually hardinfo or similar, but generic replacement is system monitor
        speaker.speak("Opening System Monitor as alternative.")
        _run_command("gnome-system-monitor", speaker)

def open_device_manager(speaker):
    if platform.system() == 'Windows':
        _run_command("start devmgmt.msc", speaker)
    else:
        speaker.speak("Device Manager is a Windows-specific tool.")

def open_registry_editor(speaker):
    if platform.system() == 'Windows':
        # Requires Admin usually
        _run_command("start regedit", speaker)
    else:
        speaker.speak("Registry Editor is Windows-specific.")
