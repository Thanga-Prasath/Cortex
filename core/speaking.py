import subprocess
import os
from core.utils.path_utils import get_base_path, get_data_path, get_user_data_path
from core.utils.config_manager import load_config
import platform
import multiprocessing
import time
import queue

def run_tts_loop(tts_queue, os_type, piper_path=None, model_path=None, is_speaking_flag=None, status_queue=None, stop_event=None):
    """
    Persistent Worker function to run TTS in a separate process.
    Initializes the engine ONCE and then waits for messages.
    """
    import os
    import json
    import audioop
    
    # Engine setup variables
    current_model_path = None
    piper_available = False
    
    # Guard: PyInstaller --noconsole sets sys.stdout/stderr to None in child
    # processes, which causes AttributeError when any print()/traceback runs.
    import sys
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')

    # Try local discovery if piper exists
    voices_dir = os.path.join(get_base_path(), 'piper_engine', 'voices')

    def resolve_model(requested_pack):
        """Find the best available model following the cascading fallback plan."""
        # 0. System Default -> Force Pyttsx3
        if requested_pack == "system_default":
            return None

        # 1. Try Requested Pack
        if requested_pack:
            p = os.path.join(voices_dir, f"{requested_pack}.onnx")
            if os.path.exists(p):
                return p
        
        # 2. If not found, fallback to System Default (return None)
        return None

    print("[OK] TTS Worker Started Ready")

    # Pre-check piper bin — guard against None before calling os.path.exists
    if piper_path and not os.path.exists(piper_path):
        piper_path = None

    while True:
        try:
            # Get item from queue
            item = tts_queue.get()
            
            if item is None: # Exit signal
                break
                
            text = item
            
            # Load Config PER UTTERANCE via deep-merge (defaults + user overrides)
            voice_rate = 175
            voice_volume = 1.0
            voice_pack = "system_default"
            # Output device relies purely on OS default via PyAudio's `output=True`
            try:
                cfg = load_config()
                voice_rate   = cfg.get("voice_rate", 175)
                voice_volume = cfg.get("voice_volume", 1.0)
                voice_pack   = cfg.get("voice_pack", "system_default")
            except: pass
            
            # Resolve Model Path live
            model_path = resolve_model(voice_pack)
            
            # Resolve Engine live
            current_piper = None
            if os_type == 'Windows':
                 for cand in ["piper_engine/piper/piper.exe", "piper_engine/piper_windows/piper/piper.exe"]:
                     cand_abs = os.path.abspath(cand)
                     if os.path.exists(cand_abs):
                         current_piper = cand_abs
                         break
            else:
                 cand_abs = os.path.abspath("piper_engine/piper/piper")
                 if os.path.exists(cand_abs):
                     current_piper = cand_abs
                     
            use_piper = bool(current_piper and model_path)
            
            # SIGNAL START
            if is_speaking_flag:
                is_speaking_flag.value = True
            
            # UI STATUS UPDATE
            if status_queue:
                status_queue.put(("SPEAKING", None))

            try: 
                if use_piper:
                    # Calculate Length Scale for Speed (inv proportional)
                    # Base 175 = 1.0. Faster rate = smaller scale.
                    # Limit to reasonable bounds
                    length_scale = 175.0 / max(50, voice_rate)
                    length_scale = max(0.5, min(2.0, length_scale))
                    
                    try:
                        import pyaudio
                        from core.alsa_error import no_alsa_error
                        import subprocess # Ensure subprocess is available for Piper playback

                        # Start Piper Process
                        piper_proc = subprocess.Popen(
                            [current_piper, '--model', model_path, '--output_raw', '--length_scale', str(length_scale)], 
                            stdin=subprocess.PIPE, 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL
                        )

                        # Initialize PyAudio (suppress ALSA errors)
                        with no_alsa_error():
                            p = pyaudio.PyAudio()
                            
                            kwargs = {
                                'format': pyaudio.paInt16,
                                'channels': 1,
                                'rate': 22050, # standard for Piper
                                'output': True
                            }
                            stream = p.open(**kwargs)

                        # Write text to Piper's stdin
                        piper_proc.stdin.write(text.encode('utf-8'))
                        piper_proc.stdin.close()

                        # Read and stream Piper's stdout to PyAudio
                        chunk_size = 1024
                        interrupted = False
                        while True:
                            # Check stop event mid-stream
                            if stop_event and stop_event.is_set():
                                interrupted = True
                                break
                            data = piper_proc.stdout.read(chunk_size)
                            if not data:
                                break
                            
                            # Apply Voice Volume
                            if voice_volume != 1.0:
                                try:
                                    data = audioop.mul(data, 2, voice_volume)
                                except: pass
                                
                            try:
                                stream.write(data)
                            except Exception as e:
                                # Writing failed (maybe stream was closed by interrupt)
                                interrupted = True
                                break
                        
                        # Cleanup resources
                        stream.stop_stream()
                        stream.close()
                        p.terminate()
                        # Terminate piper and discard remaining audio if interrupted
                        try:
                            piper_proc.kill()
                        except Exception:
                            pass
                        piper_proc.wait()

                    except Exception as e:
                        print(f"[!] Piper Playback Error: {e}")
                
                else:
                    # Initialize pyttsx3 PER UTTERANCE to avoid event loop issues
                    try:
                        import pyttsx3
                        engine = pyttsx3.init()
                        
                        # Configure Voice
                        try:
                            voices = engine.getProperty('voices')
                            if os_type == 'Windows':
                                for voice in voices:
                                    if 'zira' in voice.name.lower() or 'david' in voice.name.lower():
                                        engine.setProperty('voice', voice.id)
                                        break
                            elif os_type == 'Darwin':
                                for voice in voices:
                                    if 'samantha' in voice.name.lower() or 'alex' in voice.name.lower():
                                        engine.setProperty('voice', voice.id)
                                        break
                            
                            engine.setProperty('rate', voice_rate)
                            engine.setProperty('volume', voice_volume)
                        except Exception as e:
                            # Be less verbose about config errors to avoid spam
                            pass

                        engine.say(text)
                        engine.runAndWait()
                        
                        # Explicitly delete engine to free COM resources
                        engine.stop()
                        del engine
                        
                    except Exception as e:
                        print(f"[!] pyttsx3 Loop Error: {e}")
            
            finally:
                # UI STATUS UPDATE
                if status_queue:
                    status_queue.put(("IDLE", None))
                    
                # SIGNAL END - Ensure we reset even if error occurs
                if is_speaking_flag:
                     is_speaking_flag.value = False
            
        except Exception as e:
            print(f"[!] Worker Loop Error: {e}")
            # Reset flag just in case
            if is_speaking_flag:
                 is_speaking_flag.value = False

import random

class NaturalSpeechFormatter:
    def __init__(self):
        # 100% chance to apply a natural prefix for conversational feel
        self.apply_chance = 1.0
        self.current_intent = None
        
        # Emotionally categorized prefixes
        self.prefix_action = ["On it", "Alright", "Right away", "Okay, I'll get that started", "I'll take care of it", "Consider it done"]
        self.prefix_info = ["Sure thing", "Let me check on that", "Here you go", "Here is what I found", "Yes, sir"]
        self.prefix_confirm = ["Got it", "Done", "Understood", "All set", "I've handled that"]
        self.prefix_generic = ["Alright", "Of course", "Okay", "Yes, sir", "Certainly"]
        
        # Categorize intents for emotional mapping
        self.action_tags = ["app_open", "file_create_folder", "file_create_file", "file_move", "file_move_here", "workspace_create", "workspace_launch", "run_workflow", "run_automation_by_number", "window_snap_left", "window_snap_right", "window_minimize", "window_maximize", "window_restore", "scan_drivers", "system_scan", "dictation_mode"]
        self.info_tags = ["time", "date", "system_ip", "system_memory", "system_disk", "list_curr_dir", "system_info", "check_ports", "check_firewall", "check_connections", "system_processes", "login_history", "network_traffic", "internet_speed", "file_search", "list_automations", "clipboard_view", "list_apps", "cpu_info", "system_temp", "current_user", "system_uptime", "check_battery", "wifi_list"]
        self.confirm_tags = ["app_close", "workspace_close", "workspace_edit", "workspace_remove", "console_clear", "system_cleanup", "kill_process", "media_control", "system_power_advanced", "window_close", "window_show_desktop", "clipboard_clear", "note_take", "timer_set", "system_lock", "system_sleep", "system_restart", "system_shutdown", "volume_mute", "volume_unmute", "volume_set", "empty_bin", "take_screenshot"]
        
        # Phrases we NEVER want to prefix (e.g. self-referential or error messages)
        self.forbidden_starts = [
            "i ", "i'm ", "im ", "could not", "failed", "error", 
            "sorry", "unfortunately", "please", "what", "which",
            "who", "how", "when", "why", "are you", "do you", "is "
        ]
        
        # Hard swaps for overly robotic default lines
        self.dynamic_swaps = {
            "opening requested tool.": "Firing that up.",
            "scanning for available wi-fi networks.": "Looking for nearby networks."
        }
        
    def set_context(self, intent_tag):
        """Allow the brain to tell the formatter what kind of action is happening."""
        self.current_intent = intent_tag

    def format(self, text):
        if not text:
            return text
            
        original_lower = text.strip().lower()
        
        # 1. Exact sentence overrides
        if original_lower in self.dynamic_swaps:
            text = self.dynamic_swaps[original_lower]
            original_lower = text.strip().lower() # Update for next steps
            
        # 2. Skip if it's already a question
        if text.strip().endswith('?'):
            return text
            
        # 3. Check forbidden starters
        for f in self.forbidden_starts:
            if original_lower.startswith(f):
                return text
                
        # 4. Filter short system announcements like "Internet connection lost." 
        # from getting "On it, internet connection lost"
        if "connection" in original_lower or "battery" in original_lower:
             return text
                
        # 5. Probabilistic prefixing based on Context Emotion
        if random.random() <= self.apply_chance:
            prefix = random.choice(self.prefix_generic)
            
            if self.current_intent in self.action_tags:
                prefix = random.choice(self.prefix_action)
            elif self.current_intent in self.info_tags:
                prefix = random.choice(self.prefix_info)
            elif self.current_intent in self.confirm_tags:
                prefix = random.choice(self.prefix_confirm)
                
            return f"{prefix}, {text}"
            
        return text

class Speaker:
    def __init__(self, status_queue=None):
        """Initialize TTS engine based on the operating system."""
        self.status_queue = status_queue
        self.formatter = NaturalSpeechFormatter()
        self.os_type = platform.system()  # 'Linux', 'Windows', 'Darwin' (macOS)
        self.piper_available = False
        self.pyttsx3_available = False
        
        # Shared flag for "Is Speaking" state
        self.is_speaking_flag = multiprocessing.Value('b', False)
        
        print(f"[*] Detected OS: {self.os_type}")
        
        # Check availability
        self.piper_path = None
        self.model_path = None
        
        if self.os_type == 'Linux':
            self._check_piper()
            if not self.piper_available:
                self._check_pyttsx3()
        elif self.os_type == 'Windows':
            self._check_piper()
            if not self.piper_available:
                self._check_pyttsx3()
        else:
            self._check_pyttsx3()
            
        # Event to interrupt TTS mid-sentence
        self.stop_event = multiprocessing.Event()
        
        # Start Persistent Worker
        self.tts_queue = multiprocessing.Queue()
        self.worker_process = multiprocessing.Process(
            target=run_tts_loop, 
            args=(self.tts_queue, self.os_type, self.piper_path, self.model_path, self.is_speaking_flag, self.status_queue, self.stop_event)
        )
        self.worker_process.daemon = True # Kill when main process dies
        self.worker_process.start()

    def _check_piper(self):
        """Check Piper availability and binary path."""
        try:
            self.piper_path = None
            if self.os_type == 'Windows':
                 base = get_base_path()
                 paths = [
                     os.path.join(base, "piper_engine", "piper", "piper.exe"),
                     os.path.join(base, "piper_engine", "piper_windows", "piper", "piper.exe")
                 ]
                 for path in paths:
                     if os.path.exists(path):
                         self.piper_path = path
                         break
            else:
                 self.piper_path = os.path.join(get_base_path(), "piper_engine", "piper", "piper")
            
            if self.piper_path and os.path.exists(self.piper_path) and os.access(self.piper_path, os.X_OK):
                self.piper_available = True
                print(f"[OK] Piper TTS Binary available at {self.piper_path}")
            else:
                self.piper_available = False
                print(f"[!] Piper binary not found.")
        except Exception as e:
            print(f"[!] Error checking Piper: {e}")
            self.piper_available = False
    
    def _check_pyttsx3(self):
        """Check pyttsx3 availability."""
        try:
            import pyttsx3
            self.pyttsx3_available = True
            print(f"[OK] pyttsx3 TTS available")
        except ImportError:
            print("[!] pyttsx3 not installed.")
    
    def speak(self, text, blocking=True):
        """
        Push text to the TTS worker queue.
        'blocking' is ignored for the sake of speed, as per user request. 
        We rely on the queue to handle operations sequentially.
        """
        # Apply the NaturalSpeechFormatter to inject human timing and fillers wisely
        formatted_text = self.formatter.format(text)
        
        print(f"Cortex: {formatted_text}")
        
        # Log to Hub UI
        if self.status_queue:
            self.status_queue.put(("LOG", f"Cortex: {formatted_text}"))
        
        if not formatted_text:
            return
        
        # Main process just triggers the flag to prevent race conditions
        # The actual status update "SPEAKING" is now done by the worker 
        # to match the exact start of speech.
        
        # SIGNAL START - SYNC
        # Set flag immediately here (Main Process) to prevent race condition 
        # where Listener starts before Worker picks up the item.
        self.is_speaking_flag.value = True
             
        # Put in queue
        self.tts_queue.put(formatted_text)
        
        # REMOVED: Immediate IDLE update. 
        # We rely on the worker process to set IDLE when done.

    def stop(self):
        """Interrupt current speech immediately. Drains the TTS queue."""
        self.stop_event.set()
        # Drain any queued utterances so the assistant doesn't keep talking
        try:
            while True:
                self.tts_queue.get_nowait()
        except Exception:
            pass
        # Reset flag so the worker clears the event itself after stopping
        # We clear here because the worker loop checks, but never clears it
        import time
        time.sleep(0.15)  # Brief wait for the worker to notice the event
        self.stop_event.clear()
        self.is_speaking_flag.value = False

    def terminate(self):
        self.tts_queue.put(None)
        self.worker_process.join()

if __name__ == "__main__":
    multiprocessing.freeze_support() # Recommended for Windows
    s = Speaker()
    s.speak("System initialized. Persistent worker is running.")
    time.sleep(2) # Give it time to speak before exiting test
