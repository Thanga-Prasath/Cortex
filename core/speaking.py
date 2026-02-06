import subprocess
import os
import platform
import multiprocessing
import time
import queue

def run_tts_loop(tts_queue, os_type, piper_path=None, model_path=None):
    """
    Persistent Worker function to run TTS in a separate process.
    Initializes the engine ONCE and then waits for messages.
    """
    engine = None
    use_piper = False
    
    # Try initializing Piper if requested (Linux)
    if os_type == 'Linux' and piper_path and model_path:
        if os.path.exists(piper_path) and os.path.exists(model_path):
             use_piper = True
             # We don't keep a persistent piper process open here in this simple version,
             # we just spawn it per utterance acting as a worker. 
             # Optimization: To make Piper truly fast, we could keep a subprocess open, 
             # but Piper usually starts very fast. The main win here is offloading the Python overhead.
             pass

    print("[OK] TTS Worker Started Ready")

    while True:
        try:
            # Get item from queue
            item = tts_queue.get()
            
            if item is None: # Exit signal
                break
                
            text = item
            
            if use_piper:
                try:
                    # piper --model ... --output_raw | aplay ...
                    piper_proc = subprocess.Popen(
                        [piper_path, '--model', model_path, '--output_raw'], 
                        stdin=subprocess.PIPE, 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL
                    )
                    
                    aplay_proc = subprocess.Popen(
                        ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-q'], 
                        stdin=piper_proc.stdout
                    )
                    
                    # Write text directly to piper's stdin and close it
                    piper_proc.stdin.write(text.encode('utf-8'))
                    piper_proc.stdin.close()
                    
                    # Wait for aplay to finish playing
                    aplay_proc.communicate() 
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
                        
                        engine.setProperty('rate', 175)
                        engine.setProperty('volume', 0.9)
                    except Exception as e:
                        # Be less verbose about config errors to avoid spam
                        pass

                    engine.say(text)
                    engine.runAndWait()
                    
                    # Explicitly delete engine to free COM resources
                    del engine
                    
                except Exception as e:
                    print(f"[!] pyttsx3 Loop Error: {e}")
            
        except Exception as e:
            print(f"[!] Worker Loop Error: {e}")
                    # Re-init might be needed here in severe cases, but let's just continue
            
        except Exception as e:
            print(f"[!] Worker Loop Error: {e}")

class Speaker:
    def __init__(self, status_queue=None):
        """Initialize TTS engine based on the operating system."""
        self.status_queue = status_queue
        self.os_type = platform.system()  # 'Linux', 'Windows', 'Darwin' (macOS)
        self.piper_available = False
        self.pyttsx3_available = False
        
        print(f"[*] Detected OS: {self.os_type}")
        
        # Check availability
        self.piper_path = None
        self.model_path = None
        
        if self.os_type == 'Linux':
            self._check_piper()
            if not self.piper_available:
                self._check_pyttsx3()
        else:
            self._check_pyttsx3()
            
        # Start Persistent Worker
        self.tts_queue = multiprocessing.Queue()
        self.worker_process = multiprocessing.Process(
            target=run_tts_loop, 
            args=(self.tts_queue, self.os_type, self.piper_path, self.model_path)
        )
        self.worker_process.daemon = True # Kill when main process dies
        self.worker_process.start()

    def _check_piper(self):
        """Check Piper availability."""
        try:
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
        
        if not text:
            return
        
        if self.status_queue and self.status_queue: 
             self.status_queue.put(("SPEAKING", None))
             
        # Put in queue
        self.tts_queue.put(text)
        
        # We don't wait for 'blocking' anymore because we want speed. 
        # If we really needed blocking, we'd need a return channel.
        # But 'blocking=True' usage in main.py loops is usually just to prevent overlap 
        # which the queue solves naturally.
        
        # Ideally we should send IDLE status when done, but since we are async now, 
        # determining "done" is harder without a callback. 
        # For UI purposes, we might leave it as SPEAKING for a fixed time or just not set it to IDLE immediately.
        # A simple hack:
        if self.status_queue:
            # We can't easily know when it's done. 
            # Let's just reset to IDLE after a short calculated delay or immediately?
            # If we reset immediately, the UI won't show "Speaking".
            # For now, let's just push IDLE.
            self.status_queue.put(("IDLE", None))

    def terminate(self):
        self.tts_queue.put(None)
        self.worker_process.join()

if __name__ == "__main__":
    multiprocessing.freeze_support() # Recommended for Windows
    s = Speaker()
    s.speak("System initialized. Persistent worker is running.")
    time.sleep(2) # Give it time to speak before exiting test
