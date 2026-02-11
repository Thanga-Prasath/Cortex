import pyautogui
import os
import datetime
import platform

def take_screenshot(speaker):
    try:
        # Determine default pictures folder
        os_type = platform.system()
        if os_type == 'Windows':
            save_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
        else:
            save_dir = os.path.join(os.path.expanduser("~"), "Pictures")
            
        # Linux Dependency Check
        if os_type == 'Linux':
            import shutil
            if not shutil.which('scrot') and not shutil.which('gnome-screenshot') and not shutil.which('xwd'):
                 speaker.speak("Missing screenshot tool. Please install 'scrot' (e.g., sudo apt install scrot).")
                 return
            
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Screenshot_{timestamp}.png"
        filepath = os.path.join(save_dir, filename)
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        speaker.speak(f"Screenshot saved to Pictures folder.")
        
    except Exception as e:
        speaker.speak(f"Failed to take screenshot: {e}")
