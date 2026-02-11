import platform
import os
import subprocess
try:
    import winreg
except ImportError:
    winreg = None

def toggle_dark_mode(speaker):
    os_type = platform.system()
    
    if os_type == 'Windows':
        # Registry: HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize
        # AppsUseLightTheme, SystemUsesLightTheme (0 = Dark, 1 = Light)
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            # Read current app theme
            try:
                current_val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            except:
                current_val = 1 # Default Light
                
            # Toggle
            new_val = 0 if current_val == 1 else 1
            
            # Set both Apps and System
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, new_val)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, new_val)
            winreg.CloseKey(key)
            
            mode = "Dark" if new_val == 0 else "Light"
            speaker.speak(f"Switched to {mode} Mode.")
            
        except Exception as e:
            speaker.speak(f"Failed to toggle dark mode: {e}")

    elif os_type == 'Darwin': # macOS
        # osascript -e 'tell app "System Events" to tell appearance preferences to set dark mode to not dark mode'
        cmd = "tell application \"System Events\" to tell appearance preferences to set dark mode to not dark mode"
        try:
            subprocess.run(["osascript", "-e", cmd])
            speaker.speak("Dark mode toggled.")
        except Exception as e:
            speaker.speak(f"Error: {e}")
            
    elif os_type == 'Linux':
        # Very DE dependent. Try GNOME.
        try:
             # Check current
             current = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"], encoding='utf-8').strip()
             if 'dark' in current:
                 cmd = "gsettings set org.gnome.desktop.interface color-scheme 'default'"
                 mode = "Light"
             else:
                 cmd = "gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'"
                 mode = "Dark"
                 
             subprocess.run(cmd, shell=True)
             speaker.speak(f"Switched to {mode} Mode (GNOME).")
        except Exception:
             speaker.speak("Dark mode toggle not supported for your Linux environment yet.")
