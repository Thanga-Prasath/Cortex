from .speaking import Speaker
from .listening import Listener
from .engines.general import GeneralEngine
from .engines.system import SystemEngine
from .engines.file_manager import FileManagerEngine
from .engines.application import ApplicationEngine
from .engines.workspace import WorkspaceEngine
from .engines.automation import AutomationEngine
from .nlu import NeuralIntentModel
import platform
import sys
import os
import datetime
import random
import json
import threading
try:
    import pyautogui
except (ImportError, Exception):
    pyautogui = None

class CortexEngine:
    def __init__(self, status_queue=None, action_queue=None, reset_event=None, shutdown_event=None):
        self.status_queue = status_queue
        self.action_queue = action_queue
        self.reset_event = reset_event
        self.shutdown_event = shutdown_event
        self.speaker = Speaker(status_queue)
        self.listener = Listener(status_queue, is_speaking_flag=self.speaker.is_speaking_flag, reset_event=reset_event, shutdown_event=shutdown_event)
        
        # Load User Config
        self.user_config = self._load_user_config()
        
        # Sub-Engines
        self.general_engine = GeneralEngine(self.speaker, self.user_config)
        self.system_engine = SystemEngine(self.speaker, self.listener, self.status_queue)
        self.file_manager = FileManagerEngine(self.speaker, self.status_queue)
        self.application_engine = ApplicationEngine(self.speaker)
        self.workspace_engine = WorkspaceEngine(self.speaker, self.status_queue)
        self.automation_engine = AutomationEngine(self.speaker, self.status_queue)
        
        # Static Engine (Database-Driven)
        from .engines.static import StaticCommandEngine
        self.static_engine = StaticCommandEngine(self.speaker, self.listener)
        
        # Internal State
        self.dictation_active = False
        self.is_on_hold = False  # [NEW] Hold/Wake state
        
        # NLU Model
        self.nlu = NeuralIntentModel()
        
        # [NEW] Inject NLU Vocabulary into Hearing (Context Injection)
        vocab_str = self.nlu.get_vocabulary_phrase()
        self.listener.update_keywords(vocab_str)

        # ── [NEW] Start Action Queue Listener ──
        self.running = True
        if self.action_queue:
            import threading
            threading.Thread(target=self._action_queue_listener, daemon=True).start()
            
        # ── Start Audio Device Monitor ──
        from .audio_monitor import AudioDeviceMonitor
        self.audio_monitor = AudioDeviceMonitor(self.speaker.tts_queue, self.status_queue)
        self.audio_monitor.start()
        
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
            'scan_drivers': "Scan for driver updates",
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
            'app_close': "Close an application",
            'workspace_create': "Create a workspace",
            'workspace_launch': "Launch a workspace",
            'workspace_close': "Close workspace",
            'workspace_edit': "Edit workspace",
            'workspace_remove': "Remove workspace",
            'workspace_list': "List workspaces",
            'media_control': "Media Command",
            'system_power_advanced': "Power Command",
            'dictation_mode': "Dictation Mode",
            'window_minimize': "Minimize Window",
            'window_maximize': "Maximize Window",
            'window_restore': "Restore Window",
            'window_snap_left': "Snap Left",
            'window_snap_right': "Snap Right",
            'window_close': "Close Window",
            'window_show_desktop': "Show Desktop",
            'clipboard_view': "Read Clipboard",
            'clipboard_clear': "Clear Clipboard",
            'note_take': "Take a Note",
            'timer_set': "Set Timer",
            'run_workflow': "Run Automation",
            'list_automations': "List Automations",
            'run_automation_by_number': "Run Automation by Number",
            # --- [NEW] UX Control Intents ---
            'hold_listening': "Hold / Go Idle",
            'resume_listening': "Resume Listening",
            'stop_speaking': "Stop Speaking",
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

    def _log(self, message):
        """Helper to send log messages to the Hub UI."""
        if self.status_queue:
            self.status_queue.put(("LOG", message))
        print(f"[Log] {message}")

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

    def _action_queue_listener(self):
        """Listens for actions from the UI process and delegates them."""
        while self.running:
            try:
                import queue
                action = self.action_queue.get(timeout=1.0)
                if isinstance(action, tuple):
                    cmd, data = action
                    if cmd == "CANCEL_SEARCH":
                        if hasattr(self, 'file_manager'):
                            self.file_manager.cancel_search(data)
                    elif cmd == "UPDATE_NAME":
                        self.user_config['name'] = data
                        print(f"[Engine] User Name synced live: {data}")
                    elif cmd == "AUTOMATION_DIALOG_STATE":
                        self.automation_dialog_active = data
                        print(f"[Engine] Automation Dialog Active: {self.automation_dialog_active}")
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Error] Action listener: {e}")

    # ─────────────────────────────────────────────────────────────
    # [NEW] Background Interrupt Thread for mid-speech interruption
    # ─────────────────────────────────────────────────────────────
    def _start_interrupt_listener(self):
        """Launch a one-shot background thread that listens for stop-speaking keywords
        while the assistant is speaking. Returns immediately."""
        t = threading.Thread(target=self._interrupt_listen_thread, daemon=True)
        t.start()

    def _interrupt_listen_thread(self):
        """Worker thread: listens for 'stop talking' ONLY while is_speaking_flag is True.
        Uses a separate short listen call with a hard timeout so it doesn't block the
        main loop."""
        import time
        STOP_KEYWORDS = [
            "stop", "stop talking", "stop speaking", "shut up",
            "be quiet", "enough", "silence", "quiet", "zip it", "cancel speech"
        ]
        # Poll until speaking starts (max 1s) to avoid a race where speech hasn't begun yet
        deadline = time.time() + 1.0
        while not self.speaker.is_speaking_flag.value:
            if time.time() > deadline:
                return  # Speech never started
            time.sleep(0.05)

        # Now listen with a small timeout for an interrupt command
        transcript = self.listener.listen_for_interrupt(timeout=30)  # separate PyAudio, bypasses speaking flag
        if transcript:
            transcript = transcript.lower().strip()
            print(f"[Interrupt Thread] Heard: '{transcript}'")
            if any(kw in transcript for kw in STOP_KEYWORDS):
                print("[Interrupt Thread] Stop keyword detected! Interrupting speech.")
                self.speaker.stop()
                if self.status_queue:
                    self.status_queue.put(("LISTENING", None))

    def execute_intent(self, tag, command):
        """Helper to route intent to the correct engine."""
        self._log(f"Executing: {tag}")

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

        # 4. Workspace Engine
        if self.workspace_engine.handle_intent(tag, command):
            return True

        # 5. Automation Engine
        res = self.automation_engine.handle_intent(tag, command)
        if res == "TOGGLE_DICTATION":
             return "TOGGLE_DICTATION"
        if res:
             return True

        # 6. Static Engine (Database-Driven)
        if self.static_engine.handle_intent(tag, command):
            return True

        # 7. General Engine
        if self.general_engine.handle_intent(tag, command):
            return True
            
        return False

    def run(self):
        self.greet_user()
        
        while True:
            # Check for reset or shutdown signal from UI
            if self.reset_event and self.reset_event.is_set():
                print("[Engine] Reset signal received. Restarting...")
                return "RESTART"
            
            if self.shutdown_event and self.shutdown_event.is_set():
                print("[Engine] Shutdown signal received. Exiting...")
                return "EXIT"

            # listen() blocks safely now. Pass is_on_hold so UI knows not to show "Listening"
            command = self.listener.listen(timeout=None, is_on_hold=self.is_on_hold) 
            
            if not command:
                continue

            command = command.lower()

            # --- Dictation Mode ---
            if self.dictation_active:
                if "stop dictation" in command or "exit dictation" in command:
                    self.dictation_active = False
                    self.speaker.speak("Dictation stopped.")
                    continue
                
                if pyautogui:
                    pyautogui.write(command + " ")
                continue

            # ─────────────────────────────────────────────────────
            # [FEATURE 1] HOLD / WAKE  (checked before everything)
            # ─────────────────────────────────────────────────────
            HOLD_KEYWORDS   = ["hold", "hold on", "pause", "pause listening",
                               "stop listening", "standby", "stand by", "go idle",
                               "be quiet", "take a break", "go to sleep mode"]
            RESUME_KEYWORDS = ["listen", "wake up", "resume", "start listening",
                               "resume listening", "i am back", "come back", "attention"]

            if self.is_on_hold:
                # While on hold, ONLY respond to resume keywords
                if any(kw in command for kw in RESUME_KEYWORDS):
                    self.is_on_hold = False
                    print("[Engine] Waking up from hold.")
                    self.speaker.speak("I am listening again.")
                else:
                    print(f"[Engine] On hold — ignoring: {command}")
                continue  # Either woke up or still on hold; skip normal processing

            if any(kw in command for kw in HOLD_KEYWORDS):
                self.is_on_hold = True
                print("[Engine] Going on hold.")
                self.speaker.speak("Going on hold. Say 'Listen' to wake me up.")
                if self.status_queue:
                    self.status_queue.put(("IDLE", None))
                continue

            # --- SAFETY OVERRIDE ---
            if command in ["stop", "exit", "bye", "shutdown", "quit", "cortex stop"]:
                self.execute_intent('exit', command)
                break

            # ────────────────────────────────────────────────────
            # [FEATURE 2] Start background interrupt listener thread
            # It will detect 'stop talking' while the assistant speaks
            # ────────────────────────────────────────────────────
            self._start_interrupt_listener()

            # Predict Intent
            if self.status_queue:
                self.status_queue.put(("THINKING", None))
            
            # Log User Speech
            self._log(f"User: {command}")
            
            tag, confidence = self.nlu.predict(command)
            
            # Debug decision
            self._log(f"Predicted: {tag} ({confidence:.2f})")
            print(f"Predicted: {tag} ({confidence:.2f})")
            
            # --- UI CONTEXT OVERRIDE ---
            # When the Automation List dialog is open, words like "run one",
            # "run two" (or Whisper-transcribed homophones "to","for") should
            # be treated as run-by-number commands, NOT as app launches.
            if getattr(self, 'automation_dialog_active', False):
                import re
                _WORD_TO_NUM = {
                    "one": "1", "two": "2", "to": "2", "too": "2",
                    "three": "3", "four": "4", "for": "4",
                    "five": "5", "six": "6", "seven": "7",
                    "eight": "8", "nine": "9", "ten": "10"
                }
                words = command.lower().split()
                # Normalise homophones into digits in the command
                normalised = " ".join(_WORD_TO_NUM.get(w, w) for w in words)
                trigger_words = {"run", "start", "execute"}
                has_trigger = any(w in words for w in trigger_words)
                has_number  = bool(re.search(r'\d+', normalised))
                if has_trigger and has_number:
                    print("[Engine] Context Override: Routing to automation runner because dialog is active.")
                    tag     = "run_automation_by_number"
                    confidence = 1.0
                    command = normalised   # pass normalised cmd so engine sees digits
                    self._log("Context Override → run_automation_by_number")
            
            # --- CONTEXT DETECTION FOR LONG SPEECH ---
            # If the user said a lot of words, they might not be talking to us
            # Ask for confirmation before acting
            word_count = len(command.split())
            context_confirmed = False
            
            if word_count > 12:  # Long utterance threshold
                print(f"Long utterance detected ({word_count} words). Asking for context confirmation.")
                self.speaker.speak("Are you talking with me?")
                
                context_response = self.listener.listen(timeout=5)
                if context_response:
                    context_response = context_response.lower()
                    print(f"Context response: {context_response}")
                    
                    # Check if user confirms they were talking to the assistant
                    affirmatives = ["yes", "yeah", "yup", "sure", "of course", "definitely"]
                    if not any(word in context_response for word in affirmatives):
                        print("User was not talking to assistant. Ignoring command.")
                        self.speaker.speak("Understood. I will ignore that.")
                        continue
                    else:
                        context_confirmed = True
                        print("Context confirmed. User was talking to assistant.")
                else:
                    print("No context response. Ignoring command.")
                    continue
            
            # --- CONFIDENCE LOGIC ---
            res = None
            try:
                # Execute if high confidence or confirmed
                if confidence >= 0.85:
                     res = self.execute_intent(tag, command)
                     if res == "EXIT":
                         break
                     if res == "TOGGLE_DICTATION":
                         self.dictation_active = True
                         self.speaker.speak("Dictation mode enabled.")
                     
                elif 0.40 < confidence < 0.85:
                    # Ask for confirmation ONLY if we didn't already ask via context check
                    if context_confirmed:
                        print("Skipping confidence confirmation (context already confirmed).")
                        res = self.execute_intent(tag, command)
                        if res == "EXIT":
                            break
                        if res == "TOGGLE_DICTATION":
                            self.dictation_active = True
                            self.speaker.speak("Dictation mode enabled.")
                    else:
                        # Ask for confirmation
                        display_name = self.get_confirmation_message(tag, command)
                        self.speaker.speak(f"Did you say {display_name}?")
                    
                    # Listen for confirmation response
                    response = self.listener.listen() 
                    
                    if response:
                        response = response.lower().strip()
                        print(f"Confirmation response: {response}")
                        
                        positives = ["yes", "yeah", "yup", "sure", "correct", "do it", "yep", "affirmative", "confirm"]
                        
                        if any(word in response for word in positives):
                            res = self.execute_intent(tag, command)
                            if res == "EXIT":
                                break
                            if res == "TOGGLE_DICTATION":
                                self.dictation_active = True
                                self.speaker.speak("Dictation mode enabled.")

                        # ─────────────────────────────────────────────────────────
                        # [FEATURE 3] QUICK CORRECTION on medium confidence NO
                        #
                        # If user says plain "No" → cancel as usual (quick)
                        # If user says "No open browser" → strip the "no",
                        #   re-predict the corrected command, and execute it
                        #   immediately, skipping the cancel delay entirely.
                        # ─────────────────────────────────────────────────────────
                        elif response.startswith("no "):
                            corrected_cmd = response[3:].strip()  # Everything after "no "
                            if corrected_cmd:
                                print(f"[Quick Correction] User corrected to: '{corrected_cmd}'")
                                corr_tag, corr_conf = self.nlu.predict(corrected_cmd)
                                print(f"[Quick Correction] Predicted: {corr_tag} ({corr_conf:.2f})")
                                self._log(f"Quick Correction → {corr_tag}")
                                res = self.execute_intent(corr_tag, corrected_cmd)
                                if res == "EXIT":
                                    break
                                if res == "TOGGLE_DICTATION":
                                    self.dictation_active = True
                                    self.speaker.speak("Dictation mode enabled.")
                            else:
                                # Plain "no" with nothing after → regular cancel
                                self.speaker.speak("Cancelled.")
                                res = "CANCELLED"
                        else:
                            # Any other negative → cancel
                            self.speaker.speak("Cancelled.")
                            res = "CANCELLED"
                    else:
                        self.speaker.speak("Timeout.")
                        res = "TIMEOUT"
            
            finally:
                # Reset status to IDLE regardless of what happened
                if self.status_queue:
                    self.status_queue.put(("IDLE", None))
                
                # If we broke out (EXIT), don't continue loop
                if res == "EXIT":
                    break

            if res:
                continue

            # Fallback if low confidence or unknown tag
            if not res and res != "CANCELLED":
                self._log(f"Fallback: Checking Static Command Database for: {command}")
                # Try to handle as a static command without a specific tag
                if self.static_engine.handle_intent(None, command):
                    continue
            
            if not res:
                self.speaker.speak("I heard you, but I am not sure I understand.")



    def shutdown(self):
        """Cleanly shutdown the engine and subsystems."""
        print("[System] Shutting down...")
        if self.speaker:
            self.speaker.terminate()
        if self.listener:
            self.listener.terminate()

