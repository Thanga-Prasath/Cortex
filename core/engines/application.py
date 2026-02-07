from components.application import open_application, close_application
import threading

class ApplicationEngine:
    def __init__(self, speaker):
        self.speaker = speaker

    def handle_intent(self, intent, command):
        
        # NLU might give intents like 'app_open' or 'app_close'
        # Or we might have set it up differently. 
        # Based on the plan, we expect the main loop to pass tag/intent here.
        
        if intent == 'app_open':
            # Extract app name. 
            # heuristic: remove "open", "launch", "application", "please"
            app_name = self._extract_app_name(command, ["open", "launch", "start", "run", "application", "app"])
            if app_name:
                threading.Thread(target=self._open_app, args=(app_name,)).start()
            else:
                self.speaker.speak("Which application would you like me to open?")
            return True
            
        elif intent == 'app_close':
            app_name = self._extract_app_name(command, ["close", "quit", "exit", "terminate", "kill", "application", "app"])
            if app_name:
                threading.Thread(target=self._close_app, args=(app_name,)).start()
            else:
                self.speaker.speak("Which application would you like me to close?")
            return True
            
        return False

    def _extract_app_name(self, command, triggers):
        # Very simple extraction: remove trigger words, return rest
        words = command.split()
        filtered = [w for w in words if w.lower() not in triggers]
        return " ".join(filtered).strip()

    def _open_app(self, app_name):
        open_application(app_name, self.speaker)

    def _close_app(self, app_name):
        close_application(app_name, self.speaker)
