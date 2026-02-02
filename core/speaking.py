import subprocess
import os
import platform
import multiprocessing

def run_tts_worker(text, os_type):
    """
    Worker function to run pyttsx3 in a separate process.
    This ensures the event loop is created and destroyed cleanly for each utterance,
    preventing conflicts with other libraries (like PyAudio) or stuck loops.
    """
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
            print(f"[!] Worker Voice config error: {e}")

        engine.say(text)
        engine.runAndWait()
        
    except Exception as e:
        print(f"[!] TTS Worker Error: {e}")

class Speaker:
    def __init__(self, status_queue=None):
        """Initialize TTS engine based on the operating system."""
        self.status_queue = status_queue
        self.os_type = platform.system()  # 'Linux', 'Windows', 'Darwin' (macOS)
        self.piper_available = False
        self.pyttsx3_available = False
        self.engine = None
        
        print(f"[*] Detected OS: {self.os_type}")
        
        # Try to initialize appropriate TTS engine
        if self.os_type == 'Linux':
            self._init_piper()
            # Fallback to pyttsx3 if Piper not available
            if not self.piper_available:
                print("[*] Piper not available, falling back to pyttsx3")
                self._init_pyttsx3()
        else:
            # Windows or macOS - use pyttsx3
            self._init_pyttsx3()
    
    def _init_piper(self):
        """Initialize Piper TTS for Linux (high-quality neural TTS)."""
        try:
            self.piper_path = os.path.abspath("piper_engine/piper/piper")
            self.model_path = os.path.abspath("piper_engine/voice.onnx")
            
            # Verify paths existence
            if os.path.exists(self.piper_path) and os.path.exists(self.model_path):
                # Check if piper is executable
                if os.access(self.piper_path, os.X_OK):
                    self.piper_available = True
                    print(f"[✓] Piper TTS initialized successfully")
                else:
                    print(f"[!] Piper found but not executable at {self.piper_path}")
            else:
                if not os.path.exists(self.piper_path):
                    print(f"[!] Piper not found at {self.piper_path}")
                if not os.path.exists(self.model_path):
                    print(f"[!] Model not found at {self.model_path}")
        except Exception as e:
            print(f"[!] Error initializing Piper: {e}")
            self.piper_available = False
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 TTS for Windows/macOS/Linux fallback."""
        try:
            # We just verify it can be imported, but we won't keep an engine instance 
            # alive in the main process if we're using multiprocessing.
            import pyttsx3
            # self.engine = pyttsx3.init() # Do NOT init in main process if using MP worker
            self.pyttsx3_available = True
            print(f"[✓] pyttsx3 TTS initialized successfully")
        except ImportError:
            print("[!] pyttsx3 not installed. Install with: pip install pyttsx3")
            self.pyttsx3_available = False
        except Exception as e:
            print(f"[!] Error initializing pyttsx3: {e}")
            self.pyttsx3_available = False
    
    def _speak_piper(self, text):
        """Use Piper TTS (Linux only, high quality)."""
        try:
            # piper --model ... --output_raw | aplay ...
            piper_proc = subprocess.Popen(
                [self.piper_path, '--model', self.model_path, '--output_raw'], 
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
            
            # Clean up piper process
            piper_proc.wait()
            
        except Exception as e:
            print(f"[!] Piper TTS error: {e}")
            # Fallback to pyttsx3 if available
            if self.pyttsx3_available:
                print("[*] Falling back to pyttsx3")
                self._speak_pyttsx3(text)
    
    def _speak_pyttsx3(self, text):
        """Use pyttsx3 TTS in a separate process."""
        try:
            p = multiprocessing.Process(target=run_tts_worker, args=(text, self.os_type))
            p.start()
            p.join() # Wait for speech to finish (blocking)
        except Exception as e:
            print(f"[!] pyttsx3 TTS error: {e}")

    def speak(self, text):
        """
        Convert text to speech using the best available TTS engine.
        
        Priority:
        1. Linux: Piper (high quality) → pyttsx3 fallback
        2. Windows/macOS: pyttsx3 (native engines)
        """
        print(f"Cortex: {text}")
        
        if not text:
            return
        
        try:
            # Use Piper on Linux if available
            if self.os_type == 'Linux' and self.piper_available:
                if self.status_queue: self.status_queue.put(("SPEAKING", None))
                self._speak_piper(text)
                if self.status_queue: self.status_queue.put(("IDLE", None))
            # Use pyttsx3 on Windows/macOS or as Linux fallback
            elif self.pyttsx3_available:
                if self.status_queue: self.status_queue.put(("SPEAKING", None))
                self._speak_pyttsx3(text)
                if self.status_queue: self.status_queue.put(("IDLE", None))
            else:
                print("[!] No TTS engine available. Text printed only.")
                
        except Exception as e:
            print(f"[!] TTS Error: {e}")

if __name__ == "__main__":
    multiprocessing.freeze_support() # Recommended for Windows
    s = Speaker()
    s.speak("System initialized. Cross-platform text to speech is working.")
