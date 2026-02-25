import subprocess
import os
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
    
    # Try local discovery if piper exists
    voices_dir = os.path.join(os.getcwd(), 'piper_engine', 'voices')
    
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

    config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
    
    # Pre-check piper bin
    if not os.path.exists(piper_path):
        piper_path = None

    while True:
        try:
            # Get item from queue
            item = tts_queue.get()
            
            if item is None: # Exit signal
                break
                
            text = item
            
            # Load Config PER UTTERANCE
            voice_rate = 175
            voice_volume = 1.0
            voice_pack = "system_default"
            output_device_name = None
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        data = json.load(f)
                        voice_rate = data.get("voice_rate", 175)
                        voice_volume = data.get("voice_volume", 1.0)
                        voice_pack = data.get("voice_pack", "system_default")
                        output_device_name = data.get("output_device_name", None)
            except: pass
            
            # Resolve Model Path live
            model_path = resolve_model(voice_pack)
            use_piper = bool(piper_path and model_path)
            
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
                            [piper_path, '--model', model_path, '--output_raw', '--length_scale', str(length_scale)], 
                            stdin=subprocess.PIPE, 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL
                        )

                        # Initialize PyAudio (suppress ALSA errors)
                        with no_alsa_error():
                            p = pyaudio.PyAudio()
                            
                            output_device_index = None
                            if output_device_name:
                                import subprocess
                                import sys
                                cmd = "import pyaudio, json, sys, os; sys.stderr=open(os.devnull, 'w'); p=pyaudio.PyAudio(); print(json.dumps({'def': p.get_default_output_device_info().get('name') if p.get_device_count() else None})); p.terminate()"
                                res = subprocess.run([sys.executable, "-c", cmd], capture_output=True, text=True, timeout=2)
                                
                                true_default = None
                                if res.returncode == 0 and res.stdout.strip():
                                    try: true_default = json.loads(res.stdout.strip()).get("def")
                                    except: pass
                                    
                                if true_default != output_device_name:
                                    try: default_host_api = p.get_default_host_api_info()['index']
                                    except Exception: default_host_api = None
                                        
                                    for i in range(p.get_device_count()):
                                        info = p.get_device_info_by_index(i)
                                        if default_host_api is not None and info.get('hostApi') != default_host_api:
                                            continue
                                        if info.get('name') == output_device_name and info.get('maxOutputChannels', 0) > 0:
                                            output_device_index = i
                                            break
                            
                            kwargs = {
                                'format': pyaudio.paInt16,
                                'channels': 1,
                                'rate': 22050, # standard for Piper
                                'output': True
                            }
                            if output_device_index is not None:
                                kwargs['output_device_index'] = output_device_index
                                
                            try:
                                stream = p.open(**kwargs)
                            except Exception as e:
                                print(f"[!] Target output device unavailable, falling back to default: {e}")
                                if 'output_device_index' in kwargs:
                                    del kwargs['output_device_index']
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

class Speaker:
    def __init__(self, status_queue=None):
        """Initialize TTS engine based on the operating system."""
        self.status_queue = status_queue
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
            if self.os_type == 'Windows':
                 self.piper_path = os.path.abspath("piper_engine/piper_windows/piper/piper.exe")
            else:
                 self.piper_path = os.path.abspath("piper_engine/piper/piper")
            
            if os.path.exists(self.piper_path) and os.access(self.piper_path, os.X_OK):
                self.piper_available = True
                print(f"[OK] Piper TTS Binary available")
            else:
                self.piper_available = False
                print(f"[!] Piper binary not found at {self.piper_path}")
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
        print(f"Cortex: {text}")
        
        # Log to Hub UI
        if self.status_queue:
            self.status_queue.put(("LOG", f"Cortex: {text}"))
        
        if not text:
            return
        
        # Main process just triggers the flag to prevent race conditions
        # The actual status update "SPEAKING" is now done by the worker 
        # to match the exact start of speech.
        
        # SIGNAL START - SYNC
        # Set flag immediately here (Main Process) to prevent race condition 
        # where Listener starts before Worker picks up the item.
        self.is_speaking_flag.value = True
             
        # Put in queue
        self.tts_queue.put(text)
        
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
