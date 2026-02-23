try:
    import pyautogui
except (ImportError, Exception):
    pyautogui = None
import os
import datetime
import platform

def take_screenshot(speaker):
    try:
        # Load custom path from config
        import json
        config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
        custom_save_dir = ""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    custom_save_dir = data.get("screenshot_path", "").strip()
        except: pass

        # Determine default pictures folder
        os_type = platform.system()
        
        # 1. Custom Path from Config
        if custom_save_dir and os.path.exists(custom_save_dir):
            save_dir = custom_save_dir
            save_msg = "custom location"
        else:
            # 2. OS Default Pictures/Screenshots Folder
            if os_type == 'Windows':
                default_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
            else:
                default_dir = os.path.join(os.path.expanduser("~"), "Pictures")
                
            if os.path.exists(default_dir):
                save_dir = default_dir
                save_msg = "Pictures folder"
            else:
                # 3. Fallback to Desktop
                desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                if os.path.exists(desktop_dir):
                     save_dir = desktop_dir
                     save_msg = "Desktop"
                else:
                     # 4. Final Fallback: Current Working Directory
                     save_dir = os.path.join(os.getcwd(), "screenshots")
                     save_msg = "local screenshots folder"
                     if not os.path.exists(save_dir):
                         os.makedirs(save_dir)
            
        # Linux Dependency Check
        if os_type == 'Linux':
            import shutil
            if not shutil.which('scrot') and not shutil.which('gnome-screenshot') and not shutil.which('xwd'):
                 speaker.speak("Missing screenshot tool. Please install 'scrot' (e.g., sudo apt install scrot).")
                 return
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Screenshot_{timestamp}.png"
        filepath = os.path.join(save_dir, filename)
        
        # Take screenshot
        if not pyautogui:
            speaker.speak("Screenshot functionality is unavailable because the required library could not be initialized.")
            return

        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        # [NEW] Notify UI to copy to clipboard
        if hasattr(speaker, 'status_queue') and speaker.status_queue:
            speaker.status_queue.put(("COPY_TO_CLIPBOARD", filepath))
        
        speaker.speak(f"Screenshot saved to {save_msg} and copied to clipboard.")
        
    except Exception as e:
        speaker.speak(f"Failed to take screenshot: {e}")
