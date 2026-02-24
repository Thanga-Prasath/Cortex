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
    os_type = platform.system()
    if os_type == 'Windows':
        _run_command("start devmgmt.msc", speaker)
    elif os_type == 'Linux':
        # Try hardware info tools in order of preference
        if shutil.which("hardinfo"):
            _run_command("hardinfo", speaker)
        elif shutil.which("hardinfo2"):
            _run_command("hardinfo2", speaker)
        elif shutil.which("gnome-device-manager"):
            _run_command("gnome-device-manager", speaker)
        else:
            # Fallback: show lspci + lsusb in a terminal
            speaker.speak("Opening device listing in terminal.")
            terminal = _find_linux_terminal()
            inner = "echo '=== PCI Devices ==='; lspci; echo; echo '=== USB Devices ==='; lsusb; echo; read -p 'Press Enter to close...'"
            if terminal == "gnome-terminal":
                _run_command(f'gnome-terminal -- bash -c "{inner}"', speaker)
            elif terminal == "konsole":
                _run_command(f'konsole -e bash -c "{inner}"', speaker)
            else:
                _run_command(f'xterm -e bash -c "{inner}"', speaker)
    elif os_type == 'Darwin':
        _run_command(r"open /Applications/Utilities/System\ Information.app", speaker)

def open_registry_editor(speaker):
    os_type = platform.system()
    if os_type == 'Windows':
        # Requires Admin usually
        _run_command("start regedit", speaker)
    elif os_type == 'Linux':
        # dconf-editor is the closest Linux equivalent (GNOME settings database)
        if shutil.which("dconf-editor"):
            _run_command("dconf-editor", speaker)
        else:
            speaker.speak("dconf editor is not installed. You can install it with: sudo apt install dconf-editor, or sudo pacman -S dconf-editor.")
    elif os_type == 'Darwin':
        speaker.speak("macOS does not have a registry. Opening System Settings instead.")
        _run_command("open -a 'System Settings'", speaker)


def _find_linux_terminal():
    """Find an available terminal emulator on Linux."""
    terminals = ["gnome-terminal", "konsole", "xfce4-terminal", "mate-terminal", "xterm"]
    for t in terminals:
        if shutil.which(t):
            return t
    return "xterm"
