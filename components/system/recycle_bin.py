import platform
import subprocess
import os
import sys
import shutil

# Try to import winshell
try:
    import winshell
except ImportError:
    winshell = None

def empty_recycle_bin(speaker):
    os_type = platform.system()
    
    if os_type == 'Windows':
        speaker.speak("Emptying Recycle Bin.")
        
        # Method 1: Winshell (Preferred, no admin needed usually)
        if winshell:
            try:
                # confirm=False prevents the "Are you sure?" popup
                # show_progress=False hides the progress bar
                # sound=False prevents the recycle sound
                winshell.recycle_bin().empty(confirm=False, show_progress=True, sound=False)
                speaker.speak("Recycle Bin emptied.")
                return
            except Exception as e:
                print(f"Winshell failed: {e}")
                # Fallback to PowerShell if winshell fails
                
        # Method 2: PowerShell (Fallback)
        try:
             subprocess.run(["powershell", "-Command", "Clear-RecycleBin", "-Force", "-ErrorAction", "SilentlyContinue"], check=True)
             speaker.speak("Recycle Bin emptied successfully via PowerShell.")
        except subprocess.CalledProcessError:
             speaker.speak("Failed to empty Recycle Bin. I may need administrator privileges, or the bin is already empty.")
        except Exception as e:
             speaker.speak(f"Error emptying bin: {e}")
             
    elif os_type == 'Darwin': # macOS
        speaker.speak("Emptying Trash on macOS.")
        try:
            cmd = "tell application \"Finder\" to empty trash"
            try:
                 # Check if trash is empty first? Finder might complain if empty.
                 # 'empty trash' usually warns.
                 # To skip warning:
                 # cmd = 'tell application "Finder" to empty trash ignoring application responses'
                 pass
            except:
                 pass
                 
            subprocess.run(["osascript", "-e", cmd])
            speaker.speak("Trash emptied.")
        except Exception as e:
            speaker.speak(f"Error emptying trash: {e}")
            
    elif os_type == 'Linux':
        speaker.speak("Emptying Trash on Linux.")
        try:
            # Try trash-cli if installed
            if shutil.which("trash-empty"):
                subprocess.run(["trash-empty"], check=True)
                speaker.speak("Trash emptied.")
            else:
                 # Fallback: Manual cleanup
                 trash_path = os.path.expanduser("~/.local/share/Trash/files")
                 if os.path.exists(trash_path):
                     try:
                         import shutil
                         shutil.rmtree(trash_path)
                         os.makedirs(trash_path) # Recreation might be needed
                         speaker.speak("Trash emptied manually.")
                     except Exception as e:
                         speaker.speak(f"Error clearing trash files: {e}")
                 else:
                     speaker.speak("Trash directory not found or already empty.")
        except Exception as e:
            speaker.speak(f"Error: {e}")

