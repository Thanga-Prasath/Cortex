import subprocess
import os
import platform
import multiprocessing
import time
import queue

def run_tts_loop(tts_queue, os_type, piper_path=None, model_path=None, is_speaking_flag=None, status_queue=None):
    """
    Persistent Worker function to run TTS in a separate process.
    Initializes the engine ONCE and then waits for messages.
    """
    import os
    import json
    import audioop
    
    engine = None
    use_piper = False
    
    # Try initializing Piper if requested (Linux or Windows)
    if (os_type == 'Linux' or os_type == 'Windows') and piper_path and model_path:
        if os.path.exists(piper_path) and os.path.exists(model_path):
             use_piper = True
             if os_type == 'Windows':
                 import pyaudio


    print("[OK] TTS Worker Started Ready")

    config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')

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
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        data = json.load(f)
                        voice_rate = data.get("voice_rate", 175)
                        voice_volume = data.get("voice_volume", 1.0)
            except: pass
            
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
                        if os_type == 'Linux':
                            # piper --model ... --output_raw --length_scale ... | aplay ...
                            piper_proc = subprocess.Popen(
                                [piper_path, '--model', model_path, '--output_raw', '--length_scale', str(length_scale)], 
                                stdin=subprocess.PIPE, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL
                            )
                            
                            # Note: aplay doesn't support software volume scaling easily without -v (which is deprecated/plugin based)
                            # We could pipe through 'sox' if installed, but for now we skip volume on Linux aplay
                            # UNLESS we do python-side processing and write to aplay stdin.
                            # Let's try python-side processing for consistency if performance allows.
                            
                            aplay_proc = subprocess.Popen(
                                ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-q'], 
                                stdin=subprocess.PIPE 
                            )
                            
                            # Create a thread or just write? 
                            # If we process in python we must read piper stdout and write to aplay stdin
                            # This is complex to do while streaming.
                            # Fallback: Just ignore volume on Linux for now, only speed.
                            # Actually, we can't easily do both read/write without threads.
                            # Revert to pipe for Linux
                            
                            # WRITE TEXT
                            piper_proc.stdin.write(text.encode('utf-8'))
                            piper_proc.stdin.close()
                            
                            # READ PIPER -> WRITE APLAY
                            chunk_size = 1024
                            while True:
                                data = piper_proc.stdout.read(chunk_size)
                                if not data: break
                                # Apply Volume
                                if voice_volume != 1.0:
                                    try:
                                        data = audioop.mul(data, 2, voice_volume)
                                    except: pass
                                aplay_proc.stdin.write(data)
                                
                            aplay_proc.stdin.close()
                            aplay_proc.wait()
                            piper_proc.wait()

                        elif os_type == 'Windows':
                             # Windows: Piper -> stdout -> PyAudio
                            piper_proc = subprocess.Popen(
                                [piper_path, '--model', model_path, '--output_raw', '--length_scale', str(length_scale)], 
                                stdin=subprocess.PIPE, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL
                            )

                            p = pyaudio.PyAudio()
                            # 22050Hz is standard for most Piper voices
                            # Note: Piper sometimes output 16khz depending on voice. 
                            # Assuming 22050 based on original code.
                            stream = p.open(format=pyaudio.paInt16, channels=1, rate=22050, output=True)

                            # Write text
                            piper_proc.stdin.write(text.encode('utf-8'))
                            piper_proc.stdin.close()

                            # Read and play in chunks
                            chunk_size = 1024
                            while True:
                                data = piper_proc.stdout.read(chunk_size)
                                if not data:
                                    break
                                
                                # Apply Volume
                                if voice_volume != 1.0:
                                    try:
                                        data = audioop.mul(data, 2, voice_volume)
                                    except: pass
                                    
                                stream.write(data)
                            
                            # Clean up
                            stream.stop_stream()
                            stream.close()
                            p.terminate()
                            piper_proc.wait()

                    except Exception as e:
                        print(f"[!] Piper Error: {e}")
                
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
            
        # Start Persistent Worker
        self.tts_queue = multiprocessing.Queue()
        self.worker_process = multiprocessing.Process(
            target=run_tts_loop, 
            args=(self.tts_queue, self.os_type, self.piper_path, self.model_path, self.is_speaking_flag, self.status_queue)
        )
        self.worker_process.daemon = True # Kill when main process dies
        self.worker_process.start()

    def _check_piper(self):
        """Check Piper availability."""
        try:
            if self.os_type == 'Windows':
                 self.piper_path = os.path.abspath("piper_engine/piper_windows/piper/piper.exe")
            else:
                 self.piper_path = os.path.abspath("piper_engine/piper/piper")
            
            self.model_path = os.path.abspath("piper_engine/voice.onnx")
            
            if os.path.exists(self.piper_path) and os.path.exists(self.model_path):
                if os.access(self.piper_path, os.X_OK):
                    self.piper_available = True
                    print(f"[OK] Piper TTS available")
                else:
                    print(f"[!] Piper found but not executable")
            else:
                print(f"[!] Piper not found")
        except Exception as e:
            print(f"[!] Error checking Piper: {e}")
    
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

    def terminate(self):
        self.tts_queue.put(None)
        self.worker_process.join()

if __name__ == "__main__":
    multiprocessing.freeze_support() # Recommended for Windows
    s = Speaker()
    s.speak("System initialized. Persistent worker is running.")
    time.sleep(2) # Give it time to speak before exiting test
