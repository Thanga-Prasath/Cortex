#!/usr/bin/env python3
"""
Cortex Auto-Start Setup
Configures Cortex to automatically start when the OS boots/user logs in.
Works on Windows, Linux, and macOS.
"""

import os
import sys
import platform


def get_app_executable():
    """Get the path to the Cortex executable."""
    if getattr(sys, 'frozen', False):
        # Running as packaged app
        return sys.executable
    else:
        # Running from source
        return os.path.abspath(sys.argv[0])


def setup_windows_autostart():
    """Add Cortex to Windows startup via Registry."""
    try:
        import winreg
        app_path = get_app_executable()
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "Cortex", 0, winreg.REG_SZ, f'"{app_path}"')
        winreg.CloseKey(key)
        print("✅ Cortex added to Windows startup.")
        return True
    except Exception as e:
        print(f"❌ Failed to add to Windows startup: {e}")
        return False


def remove_windows_autostart():
    """Remove Cortex from Windows startup."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, "Cortex")
            print("✅ Cortex removed from Windows startup.")
        except FileNotFoundError:
            print("ℹ️  Cortex was not in Windows startup.")
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"❌ Failed to remove from Windows startup: {e}")
        return False


def setup_linux_autostart():
    """Add Cortex to Linux autostart via XDG autostart directory."""
    autostart_dir = os.path.expanduser("~/.config/autostart")
    desktop_file = os.path.join(autostart_dir, "cortex.desktop")

    try:
        os.makedirs(autostart_dir, exist_ok=True)
        app_path = get_app_executable()

        content = f"""[Desktop Entry]
Type=Application
Name=Cortex
Comment=AI Voice Assistant
Exec={app_path}
Icon=cortex
Terminal=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
"""
        with open(desktop_file, 'w') as f:
            f.write(content)

        os.chmod(desktop_file, 0o755)
        print("✅ Cortex added to Linux autostart.")
        print(f"   File: {desktop_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to add to Linux autostart: {e}")
        return False


def remove_linux_autostart():
    """Remove Cortex from Linux autostart."""
    desktop_file = os.path.expanduser("~/.config/autostart/cortex.desktop")
    try:
        if os.path.exists(desktop_file):
            os.remove(desktop_file)
            print("✅ Cortex removed from Linux autostart.")
        else:
            print("ℹ️  Cortex was not in Linux autostart.")
        return True
    except Exception as e:
        print(f"❌ Failed to remove from Linux autostart: {e}")
        return False


def setup_macos_autostart():
    """Add Cortex to macOS login items via LaunchAgent."""
    plist_dir = os.path.expanduser("~/Library/LaunchAgents")
    plist_file = os.path.join(plist_dir, "com.cortex.voiceassistant.plist")

    try:
        os.makedirs(plist_dir, exist_ok=True)
        app_path = get_app_executable()

        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cortex.voiceassistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""
        with open(plist_file, 'w') as f:
            f.write(content)

        # Load the agent
        os.system(f'launchctl load "{plist_file}" 2>/dev/null')
        print("✅ Cortex added to macOS login items.")
        print(f"   File: {plist_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to add to macOS autostart: {e}")
        return False


def remove_macos_autostart():
    """Remove Cortex from macOS login items."""
    plist_file = os.path.expanduser(
        "~/Library/LaunchAgents/com.cortex.voiceassistant.plist"
    )
    try:
        if os.path.exists(plist_file):
            os.system(f'launchctl unload "{plist_file}" 2>/dev/null')
            os.remove(plist_file)
            print("✅ Cortex removed from macOS login items.")
        else:
            print("ℹ️  Cortex was not in macOS login items.")
        return True
    except Exception as e:
        print(f"❌ Failed to remove from macOS autostart: {e}")
        return False


def setup_autostart():
    """Configure auto-start for the current platform."""
    os_type = platform.system()
    print(f"\n🔧 Setting up Cortex auto-start on {os_type}...\n")

    if os_type == "Windows":
        return setup_windows_autostart()
    elif os_type == "Linux":
        return setup_linux_autostart()
    elif os_type == "Darwin":
        return setup_macos_autostart()
    else:
        print(f"❌ Unsupported OS: {os_type}")
        return False


def remove_autostart():
    """Remove auto-start for the current platform."""
    os_type = platform.system()
    print(f"\n🔧 Removing Cortex auto-start on {os_type}...\n")

    if os_type == "Windows":
        return remove_windows_autostart()
    elif os_type == "Linux":
        return remove_linux_autostart()
    elif os_type == "Darwin":
        return remove_macos_autostart()
    else:
        print(f"❌ Unsupported OS: {os_type}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        remove_autostart()
    else:
        setup_autostart()
