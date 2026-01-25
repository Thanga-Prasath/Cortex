import subprocess
import os

class Speaker:
    def __init__(self):
        # Path to piper executable and model
        self.piper_path = os.path.abspath("piper_engine/piper/piper")
        self.model_path = os.path.abspath("piper_engine/voice.onnx")
        
        # Verify paths existence
        if not os.path.exists(self.piper_path):
            print(f"[!] Piper not found at {self.piper_path}")
        if not os.path.exists(self.model_path):
            print(f"[!] Model not found at {self.model_path}")

    def speak(self, text):
        """Converts text to speech using Piper (Offline Neural TTS)."""
        print(f"Sunday: {text}")
        if not text:
            return

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
            
            # Allow piper to finish writing to the pipe
            # We don't wait for piper_proc immediately because aplay handles the stream
            
            # Wait for aplay to finish playing
            aplay_proc.communicate() 
            
            # Clean up piper process calls
            piper_proc.wait()
            
        except Exception as e:
            # Fallback or error print
            # print(f"Error speaking: {e}")
            pass

if __name__ == "__main__":
    s = Speaker()
    s.speak("System initialized.")
