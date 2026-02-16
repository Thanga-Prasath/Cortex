import datetime
import json
import random
import os
import platform
import subprocess
try:
    import pyautogui
except (ImportError, Exception):
    pyautogui = None

class GeneralEngine:
    def __init__(self, speaker, user_config=None):
        self.speaker = speaker
        self.user_config = user_config if user_config else {"name": "Sir"}
        self.load_intents()

    def load_intents(self):
        self.data = {"intents": []}
        try:
            import glob
            path = os.path.join(os.getcwd(), 'data', 'intents', '*.json')
            files = glob.glob(path)
            
            for file_path in files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if 'intents' in data:
                            self.data['intents'].extend(data['intents'])
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    
        except Exception as e:
            print(f"Error loading commands: {e}")

    def handle_intent(self, tag, command=""):
        """
        Executes action based on the identified tag.
        """
        user_name = self.user_config.get('name', 'Sir')
        
        # --- Dynamic Handlers ---

        if tag == 'media_control':
            if not pyautogui:
                self.speaker.speak("I cannot control media because the required library is missing.")
                return True
                
            cmd = command.lower()
            if 'play' in cmd or 'pause' in cmd or 'resume' in cmd or 'stop' in cmd:
                pyautogui.press('playpause')
            elif 'next' in cmd or 'skip' in cmd:
                pyautogui.press('nexttrack')
            elif 'previous' in cmd or 'back' in cmd:
                pyautogui.press('prevtrack')
            elif 'volume up' in cmd or 'louder' in cmd:
                for _ in range(5): pyautogui.press('volumeup')
            elif 'volume down' in cmd or 'quieter' in cmd:
                for _ in range(5): pyautogui.press('volumedown')
            elif 'mute' in cmd or 'unmute' in cmd:
                pyautogui.press('volumemute')
                
            return True

        elif tag == 'system_power_advanced':
            cmd = command.lower()
            sys_platform = platform.system()
            
            if 'lock' in cmd:
                if sys_platform == "Windows":
                    os.system("rundll32.exe user32.dll,LockWorkStation")
                elif sys_platform == "Linux":
                    os.system("gnome-screensaver-command -l") 
                elif sys_platform == "Darwin":
                    os.system("pmset displaysleepnow")
                self.speaker.speak("Locking system.")
                
            elif 'sleep' in cmd:
                self.speaker.speak("Putting system to sleep.")
                if sys_platform == "Windows":
                    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                elif sys_platform == "Linux":
                    os.system("systemctl suspend")
                elif sys_platform == "Darwin":
                    os.system("pmset sleepnow")
                    
            elif 'monitor' in cmd or 'screen' in cmd:
                self.speaker.speak("Turning off monitor.")
                if sys_platform == "Windows":
                    # PowerShell command to sleep monitor
                    ps_cmd = "(Add-Type '[DllImport(\"user32.dll\")]public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);' -Name a -Passthru)::SendMessage(-1,0x0112,0xF170,2)"
                    subprocess.Popen(["powershell", "-command", ps_cmd])
                elif sys_platform == "Linux":
                    os.system("xset dpms force off")
                    
            elif 'hibernate' in cmd:
                self.speaker.speak("Hibernating.")
                if sys_platform == "Windows":
                    os.system("shutdown /h")
                elif sys_platform == "Linux":
                    os.system("systemctl hibernate")
            
            return True

        elif tag == 'time':
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            self.speaker.speak(f"The time is {current_time}, {user_name}.")
            return True
        
        elif tag == 'date':
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.speaker.speak(f"Today is {current_date}, {user_name}.")
            return True

        # --- Static Responses from JSON ---
        for intent in self.data['intents']:
            if intent['tag'] == tag:
                if intent.get('responses'):
                    response = random.choice(intent['responses'])
                    try:
                        formatted_response = response.format(name=user_name)
                    except Exception:
                        formatted_response = response
                    
                    self.speaker.speak(formatted_response)
                    return True
        
        return False

    def handle(self, command):
        """
        Legacy handler (Optional, kept if needed, but we rely on NLU now)
        """
        return False
