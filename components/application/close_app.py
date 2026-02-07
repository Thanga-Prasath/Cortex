import os
import subprocess
import platform

def get_platform():
    if platform.system() == "Windows":
        return "windows"
    elif platform.system() == "Darwin":
        return "macos"
    else:
        return "linux"

def close_application(app_name, speaker):
    """
    Closes the specified application.
    """
    app_name = app_name.strip()
    plat = get_platform()
    
    bin_mapping = {
        "chrome": "chrome",
        "google chrome": "chrome",
        "firefox": "firefox",
        "code": "code", 
        "vscode": "code",
        "calculator": "calc",
        "notepad": "notepad",
        "command prompt": "cmd",
        "terminal": "cmd",
        "explorer": "explorer",
        "file explorer": "explorer",
        "files": "explorer",
        "edge": "msedge",
        "microsoft edge": "msedge",
        "paint": "mspaint",
        "settings": "SystemSettings", 
        "vlc": "vlc",
        "spotify": "spotify",
        "whatsapp": "WhatsApp",
    }
    
    target_app = bin_mapping.get(app_name.lower(), app_name)
    
    print(f"[Application] Request to close: {app_name} (Target: {target_app})")

    try:
        if plat == "linux":
            # pkill searches pattern
            subprocess.run(["pkill", "-f", target_app])
            speaker.speak(f"Closing {app_name}")
            
        elif plat == "macos":
            script = f'quit app "{app_name}"' 
            subprocess.run(["osascript", "-e", script])
            speaker.speak(f"Closing {app_name}")
            
        elif plat == "windows":
            # SPECIAL CASE: File Explorer / Explorer
            # Killing explorer.exe kills the taskbar/desktop.
            # We use a safe COM-based method to close folder windows only.
            shell_names = ["explorer", "file explorer", "files", "explorer.exe"]
            if app_name.lower() in shell_names or target_app.lower() == "explorer":
                print("[Application] Using safe closing for File Explorer windows...")
                ps_cmd = "powershell -Command \"(New-Object -ComObject Shell.Application).Windows() | foreach { $_.Quit() }\""
                subprocess.run(ps_cmd, shell=True, capture_output=True)
                speaker.speak(f"Closing {app_name}")
                return

            # taskkill /IM image_name /F
            image_name = target_app
            if not image_name.lower().endswith(".exe") and "." not in image_name:
                 image_name += ".exe"
                 
            print(f"[Application] Closing Windows Process: {image_name}")
            # Try taskkill first (for exact matches like "notepad.exe")
            # If target_app was mapped (e.g. "manual mapped exe"), this works well.
            result = subprocess.run(f"taskkill /IM \"{image_name}\" /F", shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                speaker.speak(f"Closing {app_name}")
            else:
                # Universal Fallback: Close by Window Title
                # This works for "PowerPoint", "WhatsApp", "Chrome", etc. even without mapping.
                # We search for any process with a Main Window Title containing the app name.
                
                print(f"[Application] Closing by Window Title: *{app_name}*")
                ps_cmd = f"powershell -Command \"Get-Process | Where-Object {{ $_.MainWindowTitle -like '*{app_name}*' }} | Stop-Process -Force\""
                ps_res = subprocess.run(ps_cmd, shell=True, capture_output=True)
                
                if ps_res.returncode == 0:
                     # Check if we actually killed something? PS doesn't output if empty.
                     # But returncode 0 just means no error.
                     # We can trust the user's perception if window disappears.
                     speaker.speak(f"Closing {app_name}")
                else:
                    # Final fallback: Process Name fuzzy match (for background apps without window title)
                    ps_cmd_2 = f"powershell -Command \"Get-Process | Where-Object {{ $_.Name -like '*{target_app}*' }} | Stop-Process -Force\""
                    ps_res_2 = subprocess.run(ps_cmd_2, shell=True, capture_output=True)
                    
                    if ps_res_2.returncode == 0:
                         speaker.speak(f"Closing {app_name}")
                    else:
                        speaker.speak(f"I could not close {app_name}.")
            
    except Exception as e:
        print(f"[Error] Failed to close {app_name}: {e}")
        speaker.speak(f"I encountered an issue closing {app_name}.")
