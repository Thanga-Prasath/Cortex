from .speaking import Speaker
from .listening import Listener
from .engines.general import GeneralEngine
from .engines.system import SystemEngine
from .engines.file_manager import FileManagerEngine
from .engines.application import ApplicationEngine
from .nlu import NeuralIntentModel
import platform
import sys
import os
import datetime
import random
import json

class CortexEngine:
    def __init__(self, status_queue=None):
        self.status_queue = status_queue
        self.speaker = Speaker(status_queue)
        self.listener = Listener(status_queue, is_speaking_flag=self.speaker.is_speaking_flag)
        
        # Load User Config
        self.user_config = self._load_user_config()
        
        # Sub-Engines
        self.general_engine = GeneralEngine(self.speaker, self.user_config)
        self.system_engine = SystemEngine(self.speaker, self.listener)
        self.file_manager = FileManagerEngine(self.speaker)
        self.application_engine = ApplicationEngine(self.speaker)
        
        # NLU Model
        self.nlu = NeuralIntentModel()
        
        # [NEW] Inject NLU Vocabulary into Hearing (Context Injection)
        vocab_str = self.nlu.get_vocabulary_phrase()
        self.listener.update_keywords(vocab_str)
        
        # Tag to Human Readable Name Mapping for Confirmations
        self.intent_names = {
            'greet': "Greeting",
            'time': "Check the time",
            'date': "Check the date",
            'system_ip': "Check IP address",
            'system_memory': "Check RAM usage",
            'system_disk': "Check disk space",
            'list_curr_dir': "List files in directory",
            'system_info': "Check system information",
            'system_scan': "Run a security scan",
            'check_ports': "Check open ports",
            'check_firewall': "Check firewall status",
            'console_clear': "Clear the console",
            'check_connections': "Check network connections",
            'system_processes': "Monitor system processes",
            'login_history': "Check login history",
            'network_traffic': "Monitor network traffic",
            'internet_speed': "Run an internet speed test",
            'system_cleanup': "Perform system cleanup",
            'kill_process': "Terminate a process",
            'file_create_folder': "Create a new folder",
            'file_create_file': "Create a new file",
            'file_move': "Move files",
            'file_move_here': "Paste files here",
            'file_search': "Search for a file",
            'app_open': "Open an application",
            'app_close': "Close an application"
        }

    def get_confirmation_message(self, tag, command):
        """Generates a refined confirmation message with parameters if available."""
        # Mapping for parametric intents
        if tag == 'app_open':
            name = self._extract_param(command, ["open", "launch", "start", "run", "application", "app"])
            return f"Open {name}" if name else "Open an application"
        elif tag == 'app_close':
            name = self._extract_param(command, ["close", "quit", "exit", "terminate", "kill", "application", "app"])
            return f"Close {name}" if name else "Close an application"
        elif tag == 'file_search':
            name = self._extract_param(command, ["search", "find", "look for", "locate", "file", "folder"])
            return f"Search for {name}" if name else "Search for a file"
            
        # Default to standard mapping
        return self.intent_names.get(tag, tag.replace("_", " "))

    def _extract_param(self, command, triggers):
        """Simple extraction helper for confirmation messages."""
        words = command.lower().split()
        filtered = [w for w in words if w not in triggers]
        return " ".join(filtered).strip().title()

    def _load_user_config(self):
        """Loads user configuration from JSON file."""
        config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return {"name": "Sir"}

    def _save_user_config(self):
        """Saves current user configuration to JSON file."""
        config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(self.user_config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def _extract_name(self, command):
        """Extracts name from change_name commands."""
        prefixes = ["call me ", "change my name to ", "change name to ", "my name is ", "i am "]
        for prefix in prefixes:
            if command.startswith(prefix):
                 name = command[len(prefix):].strip()
                 if name:
                     return name.title()
        return None

    def greet_user(self):
        hour = datetime.datetime.now().hour
        name = self.user_config.get('name', 'Sir')
        
        if 0 <= hour < 12:
            greeting = f"Good Morning, {name}."
        elif 12 <= hour < 18:
            greeting = f"Good Afternoon, {name}."
        else:
            greeting = f"Good Evening, {name}."
            
        suffixes = [
            "I am ready to help you.",
            "It is lovely to see you again.",
            "How can I be of service?",
            "I hope you are having a wonderful day."
        ]
        
        self.speaker.speak(f"{greeting} {random.choice(suffixes)}")

    def execute_intent(self, tag, command):
        """Helper to route intent to the correct engine."""

        # Check Global/System exits first
        if tag == 'exit':
            name = self.user_config.get('name', 'Sir')
            self.speaker.speak(random.choice([
                f"It has been a pleasure serving you, {name}. Have a wonderful rest of your day.",
                f"Closing down now. I look forward to our next interaction. Goodbye, {name}.",
                f"Shutting down systems. Take care, {name}, and see you soon.",
                f"As you wish, {name}. I hope I was helpful today. Goodbye.",
                f"Going offline. Do not hesitate to call upon me whenever you need. Farewell, {name}."
            ]))
            return "EXIT"

        if tag == 'change_name':
            new_name = self._extract_name(command)
            if new_name:
                self.user_config['name'] = new_name
                self._save_user_config()
                self.speaker.speak(f"I will call you {new_name} from now on.")
            else:
                self.speaker.speak("I didn't catch the name. What should I call you?")
            return True

        # Routing: Pass Tag to Engines
        # 1. System Engine (Check first for critical commands)
        if self.system_engine.handle_intent(tag, command):
            return True

        # 2. File Manager Engine
        if self.file_manager.handle_intent(tag, command):
            return True

        # 3. Application Engine
        if self.application_engine.handle_intent(tag, command):
            return True

        # 4. General Engine
        if self.general_engine.handle_intent(tag):
            return True
            
        return False

    def run(self):
        self.greet_user()
        
        while True:
            # listen() blocks safely now
            command = self.listener.listen()
            
            if not command:
                continue

            command = command.lower()

            # --- SAFETY OVERRIDE ---
            if command in ["stop", "exit", "bye", "shutdown", "quit", "cortex stop"]:
                self.execute_intent('exit', command)
                break

            # Predict Intent
            if self.status_queue:
                self.status_queue.put(("THINKING", None))
            tag, confidence = self.nlu.predict(command)
            
            # Debug decision
            print(f"Predicted: {tag} ({confidence:.2f})")
            
            # --- CONFIDENCE LOGIC ---
            confirm_needed = False
            if 0.40 < confidence < 0.85:
                # Ask for confirmation
                display_name = self.get_confirmation_message(tag, command)
                self.speaker.speak(f"Did you say {display_name}?")
                
                # Listen for response
                response = self.listener.listen()
                if response:
                    response = response.lower()
                    print(f"Confirmation response: {response}")
                    
                    positives = ["yes", "yeah", "yup", "sure", "correct", "do it", "yep", "affirmative"]
                    negatives = ["no", "nope", "not really", "wrong", "stop", "never mind", "incorrect"]
                    
                    if any(word in response for word in positives):
                        print("Confirmation: Positive")
                        # Proceed with execution
                        pass 
                    elif any(word in response for word in negatives):
                        print("Confirmation: Negative")
                        continue # Go back to listening
                    else:
                        print("Confirmation: Unknown/Idle")
                        continue # Go back to listening
                else:
                    print("Confirmation: Timeout/Idle")
                    continue

            # Execute if high confidence or confirmed
            if confidence >= 0.85 or (0.40 < confidence < 0.85): # Already passed confirmation if in (0.4, 0.85) block
                res = self.execute_intent(tag, command)
                if res == "EXIT":
                    break
                if res:
                    continue

            # Fallback if low confidence or unknown tag
            padded_cmd = f" {command} "
            
            # Fuzzy Matching for Common Mishearings
            if confidence <= 0.40:
                from difflib import SequenceMatcher
                
                def is_similar(a, b, threshold=0.85):
                     return SequenceMatcher(None, a, b).ratio() > threshold
                
                if is_similar(command, "exceed") or is_similar(command, "exist") or is_similar(command, "exact"):
                     tag = 'exit'
                     confidence = 0.95
                     print(f"Fuzzy Match: '{command}' -> {tag}")
                elif "system in" in command and ("full" in command or "four" in command or "fo" in command):
                     tag = 'system_info'
                     confidence = 0.95
                     print(f"Fuzzy Match: '{command}' -> {tag}")

            if confidence <= 0.40:
                # (Keyword matching logic remains, setting confidence to 1.0 for matches)
                if ' memory ' in padded_cmd or ' ram ' in padded_cmd:
                     tag = 'system_memory'
                     confidence = 1.0
                elif ' ip ' in padded_cmd or ' address ' in padded_cmd or ' network ' in padded_cmd:
                     tag = 'system_ip'
                     confidence = 1.0
                elif ' disk ' in padded_cmd or ' storage ' in padded_cmd or ' space ' in padded_cmd:
                     tag = 'system_disk'
                     confidence = 1.0
                elif ' create ' in padded_cmd or ' make ' in padded_cmd or ' new ' in padded_cmd:
                     if ' folder ' in padded_cmd or ' directory ' in padded_cmd:
                         tag = 'file_create_folder'
                         confidence = 1.0
                     elif ' file ' in padded_cmd:
                         tag = 'file_create_file'
                         confidence = 1.0
                elif ' move ' in padded_cmd or ' transfer ' in padded_cmd:
                     tag = 'file_move'
                     confidence = 1.0
                elif ' search ' in padded_cmd or ' find ' in padded_cmd or ' locate ' in padded_cmd:
                     tag = 'file_search'
                     confidence = 1.0
                elif ' list ' in padded_cmd or (' show ' in padded_cmd and ' file ' in padded_cmd):
                     tag = 'list_curr_dir'
                     confidence = 1.0
                elif ' clear ' in padded_cmd and ' console ' in padded_cmd:
                     tag = 'console_clear'
                     confidence = 1.0
                elif ' scan ' in padded_cmd or ' virus ' in padded_cmd or ' security ' in padded_cmd:
                     tag = 'system_scan'
                     confidence = 1.0
                elif ' port ' in padded_cmd or ' ports ' in padded_cmd:
                     tag = 'check_ports'
                     confidence = 1.0
                elif ' firewall ' in padded_cmd:
                     tag = 'check_firewall'
                     confidence = 1.0
                elif ' system ' in padded_cmd and (' info ' in padded_cmd or ' specs ' in padded_cmd or ' os ' in padded_cmd or ' in form ' in padded_cmd or ' profile ' in padded_cmd or ' details ' in padded_cmd):
                     tag = 'system_info'
                     confidence = 1.0
                elif ' connections ' in padded_cmd or ' talking to ' in padded_cmd:
                     tag = 'check_connections'
                     confidence = 1.0
                elif ' process ' in padded_cmd or ' task manager ' in padded_cmd or ' top ' in padded_cmd or ' running ' in padded_cmd:
                     tag = 'system_processes'
                     confidence = 1.0
                elif ' history ' in padded_cmd and (' login ' in padded_cmd or ' user ' in padded_cmd or ' who ' in padded_cmd):
                     tag = 'login_history'
                     confidence = 1.0
                elif (' internet ' in padded_cmd or ' speed ' in padded_cmd or ' fast ' in padded_cmd) and (' test ' in padded_cmd or ' check ' in padded_cmd or ' run ' in padded_cmd):
                     tag = 'internet_speed'
                     confidence = 1.0
                elif (' internet ' in padded_cmd or ' traffic ' in padded_cmd or ' net ' in padded_cmd) and (' usage ' in padded_cmd or ' monitor ' in padded_cmd):
                     tag = 'network_traffic'
                     confidence = 1.0
                elif (' kill ' in padded_cmd or ' close ' in padded_cmd or ' terminate ' in padded_cmd) and (' system ' not in padded_cmd):
                     if ' application ' in padded_cmd or ' app ' in padded_cmd:
                         tag = 'app_close'
                         confidence = 1.0
                     else:
                         tag = 'kill_process'
                         confidence = 1.0
                elif ' open ' in padded_cmd or ' launch ' in padded_cmd or ' start ' in padded_cmd or ' run ' in padded_cmd:
                     tag = 'app_open'
                     confidence = 1.0

            # Re-execute if keyword match set confidence to 1.0
            if confidence >= 0.85:
                res = self.execute_intent(tag, command)
                if res == "EXIT":
                    break
                if res:
                    continue

            self.speaker.speak("I heard you, but I am not sure I understand.")

            self.speaker.speak("I heard you, but I am not sure I understand.")

    def shutdown(self):
        """Cleanly shutdown the engine and subsystems."""
        print("[System] Shutting down...")
        if self.speaker:
            self.speaker.terminate()

