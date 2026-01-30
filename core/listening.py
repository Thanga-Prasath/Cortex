try:
    import json
    import pyaudio

    import os
    import wave
    import time
    import numpy as np
    from faster_whisper import WhisperModel
    from .alsa_error import no_alsa_error
except ImportError as e:
    print(f"\n[CRITICAL] Missing Dependency: {e.name}")
    print(f"Please run: pip install -r requirements.txt\n")
    raise e

class Listener:
    def __init__(self):
        self.model_size = "base.en"
        print(f"[System] Loading Whisper Model ({self.model_size})...")
        
        # Suppress ALSA/Jack errors
        with no_alsa_error():
            # Run on CPU with INT8 quantization for speed/compatibility
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            self.p = pyaudio.PyAudio()

        self.THRESHOLD = 1000  # Default, adjusted by calibration
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.SILENCE_LIMIT = 1.5 # Seconds of silence to stop recording

        self.calibrate_noise()

    def calibrate_noise(self):
        """Measures ambient noise level to set dynamic threshold."""
        print("Calibrating background noise... (Please stay quiet)")
        try:
            with no_alsa_error():
                stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
            
            stream.start_stream()
            
            noise_levels = []
            for _ in range(30): # Listen for ~1.5 second
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                # rms = audioop.rms(data, 2) - Replaced for Python 3.13 compatibility
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                rms = np.sqrt(np.mean(samples**2))
                noise_levels.append(rms)
            
            stream.stop_stream()
            stream.close()
            
            avg_noise = sum(noise_levels) / len(noise_levels)
            self.THRESHOLD = avg_noise * 1.3 # Set threshold 30% above noise floor
            # Clamp minimum threshold to avoid super sensitivity
            if self.THRESHOLD < 300: self.THRESHOLD = 300
            
            print(f"Calibration Complete. Threshold set to: {self.THRESHOLD:.2f} (Avg Noise: {avg_noise:.2f})")
            
        except Exception as e:
            print(f"Calibration failed: {e}. Using default threshold.")
            self.THRESHOLD = 1000

    def listen(self):
        """Records audio until silence and transcribes with Whisper."""
        try:
            with no_alsa_error():
                stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
            
            print("Listening...", end="", flush=True)

            # 1. Wait for speech to start (Voice Activity Detection)
            frames = []
            started = False
            last_speech_time = time.time()
            
            while True:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                # rms = audioop.rms(data, 2) - Replaced for Python 3.13 compatibility
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                rms = np.sqrt(np.mean(samples**2))
                
                if not started:
                    if rms > self.THRESHOLD:
                        started = True
                        print("\rListening... (Speech detected)", end="", flush=True)
                        frames.append(data)
                        last_speech_time = time.time()
                    # Else: discard silence before speech
                else:
                    frames.append(data)
                    if rms > self.THRESHOLD:
                        last_speech_time = time.time()
                    
                    # Stop if silence > SILENCE_LIMIT
                    if time.time() - last_speech_time > self.SILENCE_LIMIT:
                        break
                    
                    # Hard limit for command length (e.g., 10 seconds)
                    if len(frames) * self.CHUNK / self.RATE > 10:
                         break
            
            stream.stop_stream()
            stream.close()

            # Process in-memory
            # Convert raw bytes to numpy array (float32, normalized)
            audio_data = b''.join(frames)
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Transcribe
            # print("\rProcessing...             ", end="", flush=True)
            # Beam size 1 is faster (greedy decoding), temp 0 for deterministic
            segments, info = self.model.transcribe(audio_np, beam_size=1, temperature=0, language="en")
            
            full_text = ""
            for segment in segments:
                full_text += segment.text
            
            full_text = full_text.strip().lower()

            # Filter/Validation Logic
            if not full_text:
                print(f"\rListening... (No speech)        ", end="", flush=True)
                return ""

            # Remove punctuation (Whisper adds it)
            full_text = full_text.replace(".", "").replace("?", "").replace(",", "").replace("!", "")
            
            # Whitelist/Filter check
            words = full_text.split()
            # Important: Included the security keywords
            important_keywords = [
                "time", "date", "hello", "hi", "hey", "stop", "exit", "bye", "quit", "sunday", "help", 
                "scan", "security", "firewall", "ports", "list", "check", "system"
            ]
            
            # Relaxed filter: Allow if > 1 word OR is a keyword
            is_valid = len(words) > 1 or (len(words) == 1 and words[0] in important_keywords)
            
            if is_valid:
                print(f"\rUser: {full_text}" + " " * 20)
                return full_text
            else:
                 print(f"\rListening... (Ignored '{full_text}')", end="", flush=True)
                 return ""

        except KeyboardInterrupt:
            return "exit"
        except Exception as e:
            print(f"\nError in listening: {e}")
            return ""

if __name__ == "__main__":
    l = Listener()
    while True:
        l.listen()
