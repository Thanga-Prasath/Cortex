from .speaking import Speaker
from .listening import Listener
from .engines.general import GeneralEngine
from .engines.system import SystemEngine
from .engines.file_manager import FileManagerEngine
from .nlu import NeuralIntentModel
import platform
import sys
import os
import datetime
import random

class CortexEngine:
    def __init__(self, status_queue=None):
        self.status_queue = status_queue
        self.speaker = Speaker(status_queue)
        self.listener = Listener(status_queue)
        
        # Sub-Engines
        self.general_engine = GeneralEngine(self.speaker)
        self.system_engine = SystemEngine(self.speaker, self.listener)
        self.file_manager = FileManagerEngine(self.speaker)
        
        # NLU Model
        self.nlu = NeuralIntentModel()
        
        # OS Detection
        self.system_os = platform.system()
        if hasattr(sys, 'getandroidapilevel') or 'ANDROID_ARGUMENT' in os.environ:
             self.system_os = 'Android'
             
        print(f"[System] Detected OS: {self.system_os}")
        if self.system_os == 'Android':
            print("[Warning] Android is not officially supported.")

    def greet_user(self):
        hour = datetime.datetime.now().hour
        if 0 <= hour < 12:
            greeting = "Good Morning, Sir."
        elif 12 <= hour < 18:
            greeting = "Good Afternoon, Sir."
        else:
            greeting = "Good Evening, Sir."
            
        suffixes = [
            "I am ready to help you.",
            "It is lovely to see you again.",
            "How can I be of service?",
            "I hope you are having a wonderful day."
        ]
        
        self.speaker.speak(f"{greeting} {random.choice(suffixes)}")

    def run(self):
        self.greet_user()
        
        while True:
            # Add a small delay/checking could be here, but listen() blocks safely now
            command = self.listener.listen()
            
            if not command:
                continue

            command = command.lower()

            # Predict Intent
            if self.status_queue:
                self.status_queue.put(("THINKING", None))
            tag, confidence = self.nlu.predict(command)
            
            # --- SAFETY OVERRIDE ---
            # Even if NLU confidence is low, strictly obey specific global commands
            # This fixes the "exit not working" issue if the model isn't sure.
            if command in ["stop", "exit", "bye", "shutdown", "quit", "cortex stop"]:
                self.speaker.speak(random.choice([
                    "It has been a pleasure serving you, Sir. Have a wonderful rest of your day.",
                    "Closing down now. I look forward to our next interaction. Goodbye, Sir.",
                    "Shutting down systems. Take care, Sir, and see you soon.",
                    "As you wish, Sir. I hope I was helpful today. Goodbye.",
                    "Going offline. Do not hesitate to call upon me whenever you need. Farewell, Sir."
                ]))
                break
            
            # Debug decision (Optional)
            print(f"Predicted: {tag} ({confidence:.2f})")
            
            if confidence > 0.40: # Lowered threshold based on verification (hello ~ 0.47)
                
                # Check Global/System exits first if handled by NLU
                if tag == 'exit':
                    self.speaker.speak(random.choice([
                        "It has been a pleasure serving you, Sir. Have a wonderful rest of your day.",
                        "Closing down now. I look forward to our next interaction. Goodbye, Sir.",
                        "Shutting down systems. Take care, Sir, and see you soon.",
                        "As you wish, Sir. I hope I was helpful today. Goodbye.",
                        "Going offline. Do not hesitate to call upon me whenever you need. Farewell, Sir."
                    ]))
                    break

                # Routing: Pass Tag to Engines
                
                # 1. System Engine (Check first for critical commands)
                if self.system_engine.handle_intent(tag):
                    continue

                # 2. File Manager Engine
                if self.file_manager.handle_intent(tag, command):
                    continue

                # 3. General Engine
                if self.general_engine.handle_intent(tag):
                    continue
            
            # Fallback if low confidence or unknown tag
            # Try rough keyword matching for poor speech recognition results
            # Added spaces to avoid partial matches (e.g. "grammar" -> "ram")
            padded_cmd = f" {command} "
            
            if confidence <= 0.40:
                if ' memory ' in padded_cmd or ' ram ' in padded_cmd:
                     tag = 'system_memory'
                     confidence = 1.0 # Override
                     print(f"Fallback: Deteced 'memory/ram' -> {tag}")
                elif ' ip ' in padded_cmd or ' address ' in padded_cmd or ' network ' in padded_cmd:
                     tag = 'system_ip'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'ip/address' -> {tag}")
                elif ' disk ' in padded_cmd or ' storage ' in padded_cmd or ' space ' in padded_cmd:
                     tag = 'system_disk'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'disk/storage' -> {tag}")
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
                     print(f"Fallback: Deteced 'file/list' -> {tag}")
                elif ' clear ' in padded_cmd and ' console ' in padded_cmd: # "clear console"
                     tag = 'console_clear'
                     confidence = 1.0
                elif ' scan ' in padded_cmd or ' virus ' in padded_cmd or ' security ' in padded_cmd:
                     tag = 'system_scan'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'scan/security' -> {tag}")
                elif ' port ' in padded_cmd or ' ports ' in padded_cmd:
                     tag = 'check_ports'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'port' -> {tag}")
                elif ' firewall ' in padded_cmd:
                     tag = 'check_firewall'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'firewall' -> {tag}")
                elif ' system ' in padded_cmd and (' info ' in padded_cmd or ' specs ' in padded_cmd or ' os ' in padded_cmd or ' in form ' in padded_cmd or ' profile ' in padded_cmd or ' details ' in padded_cmd):
                     tag = 'system_info'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'system info' -> {tag}")
                elif ' connections ' in padded_cmd or ' talking to ' in padded_cmd:
                     tag = 'check_connections'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'connections' -> {tag}")
                elif ' process ' in padded_cmd or ' task manager ' in padded_cmd or ' top ' in padded_cmd or ' running ' in padded_cmd:
                     tag = 'system_processes'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'processes' -> {tag}")
                elif ' history ' in padded_cmd and (' login ' in padded_cmd or ' user ' in padded_cmd or ' who ' in padded_cmd):
                     tag = 'login_history'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'login history' -> {tag}")
                elif (' internet ' in padded_cmd or ' speed ' in padded_cmd or ' fast ' in padded_cmd) and (' test ' in padded_cmd or ' check ' in padded_cmd or ' run ' in padded_cmd):
                     tag = 'internet_speed'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'internet speed' -> {tag}")
                elif (' internet ' in padded_cmd or ' traffic ' in padded_cmd or ' net ' in padded_cmd) and (' usage ' in padded_cmd or ' monitor ' in padded_cmd):
                     tag = 'network_traffic'
                     confidence = 1.0
                     print(f"Fallback: Deteced 'network traffic' -> {tag}")
                elif (' kill ' in padded_cmd or ' close ' in padded_cmd or ' terminate ' in padded_cmd) and (' system ' not in padded_cmd): # Avoid "clean system" conflict
                     tag = 'kill_process'
                     confidence = 1.0
                     print(f"Fallback: Detected 'kill process' -> {tag}")
            
            # Re-check confidence after fallback
            if confidence > 0.40:
                # Check Global/System exits first if handled by NLU
                if tag == 'exit':
                    self.speaker.speak(random.choice([
                        "It has been a pleasure serving you, Sir. Have a wonderful rest of your day.",
                        "Closing down now. I look forward to our next interaction. Goodbye, Sir.",
                        "Shutting down systems. Take care, Sir, and see you soon.",
                        "As you wish, Sir. I hope I was helpful today. Goodbye.",
                        "Going offline. Do not hesitate to call upon me whenever you need. Farewell, Sir."
                    ]))
                    break
                    
                # Routing: Pass Tag to Engines
                
                # 1. System Engine (Check first for critical commands)
                if self.system_engine.handle_intent(tag, command):
                    continue

                # 2. File Manager Engine
                if self.file_manager.handle_intent(tag, command):
                    continue

                # 3. General Engine
                if self.general_engine.handle_intent(tag):
                    continue

            self.speaker.speak("I heard you, but I am not sure I understand.")
