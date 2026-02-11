import platform
import subprocess
import os
try:
    import winreg
except ImportError:
    winreg = None

def toggle_hidden_files(speaker, show=None):
    """
    show: True to show, False to hide, None to toggle (not implemented yet for all)
    """
    os_type = platform.system()
    
    if os_type == 'Windows':
        # Registry: HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced
        # Value: Hidden (1 = show, 2 = hide)
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            current_val, _ = winreg.QueryValueEx(key, "Hidden")
            
            if show is None:
                # Toggle
                new_val = 2 if current_val == 1 else 1
            else:
                new_val = 1 if show else 2
                
            winreg.SetValueEx(key, "Hidden", 0, winreg.REG_DWORD, new_val)
            winreg.CloseKey(key)
            
            # Restart Explorer to apply changes immediately? 
            # Often changes are immediate in Explorer, but sometimes needs refresh.
            # We won't kill explorer as it disrupts user. 
            # We can broadcast a setting change message but that requires ctypes.
            
            status = "visible" if new_val == 1 else "hidden"
            speaker.speak(f"Hidden files are now {status}.")
            
        except Exception as e:
            speaker.speak(f"Failed to toggle hidden files: {e}")

    elif os_type == 'Darwin': # macOS
        # defaults write com.apple.finder AppleShowAllFiles -bool true
        try:
            val = "true" if show else "false"
            if show is None:
                # Check current
                curr = subprocess.check_output(["defaults", "read", "com.apple.finder", "AppleShowAllFiles"], encoding='utf-8').strip()
                val = "false" if curr == "1" or curr.lower() == "true" else "true"
            
            subprocess.run(["defaults", "write", "com.apple.finder", "AppleShowAllFiles", "-bool", val])
            # Restart Finder
            subprocess.run(["killall", "Finder"])
            
            status = "visible" if val == "true" else "hidden"
            speaker.speak(f"Hidden files are now {status}. Finder has been restarted.")
        except Exception as e:
            speaker.speak(f"Failed to toggle hidden files: {e}")

    elif os_type == 'Linux':
        # GNOME: gsettings set org.gtk.Settings.FileChooser show-hidden true
        # Files (Nautilus): gsettings set org.gnome.nautilus.preferences show-hidden-files true
        speaker.speak("Toggling hidden files on Linux depends on your Desktop Environment. I will try for GNOME.")
        try:
            # Check current
            # validation needed. Assuming toggle for now.
             subprocess.run("gsettings set org.gnome.nautilus.preferences show-hidden-files $(gsettings get org.gnome.nautilus.preferences show-hidden-files | grep -q 'true' && echo 'false' || echo 'true')", shell=True)
             speaker.speak("Toggled hidden files for Nautilus.")
        except Exception as e:
             speaker.speak(f"Failed: {e}")
