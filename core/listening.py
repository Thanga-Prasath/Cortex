try:
    import json
    import pyaudio

    import os
    import wave
    import time
    import numpy as np
    import threading
    from faster_whisper import WhisperModel
    from .alsa_error import no_alsa_error
except ImportError as e:
    print(f"\n[CRITICAL] Missing Dependency: {e.name}")
    print(f"Please run: pip install -r requirements.txt\n")
    raise e

class Listener:
    def __init__(self, status_queue=None, is_speaking_flag=None, reset_event=None):
        self.status_queue = status_queue
        self.is_speaking_flag = is_speaking_flag
        self.reset_event = reset_event
        # Use base.en for faster speed (trade-off: slightly less accurate than small)
        # small.en is ~461MB, base.en is ~142MB
        self.model_size = "base.en"
        self.model = None
        self.p = None
        
        print(f"[System] Loading Whisper Model ({self.model_size})...")
        print("[System] This should take just a few seconds...")
        
        # Try to load the model with better error handling
        try:
            with no_alsa_error():
                # Run on CPU with INT8 quantization for speed/compatibility
                # num_workers=1 to avoid threading issues
                
                print("[System] Checking for local Whisper model...")
                try:
                    # 1. Try to load from local cache first (FAST)
                    self.model = WhisperModel(
                        self.model_size, 
                        device="cpu", 
                        compute_type="int8",
                        num_workers=1,
                        local_files_only=True 
                    )
                    print("[✓] Found local model cache.")
                except Exception:
                    # 2. If not found, download it (SLOW but necessary once)
                    print(f"[!] Local model not found. Downloading {self.model_size} (approx 140MB)...")
                    print("[!] This happens only once. Please wait...")
                    self.model = WhisperModel(
                        self.model_size, 
                        device="cpu", 
                        compute_type="int8",
                        num_workers=1,
                        local_files_only=False
                    )
                
                self.p = pyaudio.PyAudio()
            
            print("[✓] Whisper Model loaded successfully!")
            
        except Exception as e:
            print(f"\n[ERROR] Failed to load Whisper model: {e}")
            print("[SOLUTION] Try these fixes:")
            print("  1. Download the model first: python -c 'from faster_whisper import WhisperModel; WhisperModel(\"tiny.en\")'")
            print("  2. Clear the model cache: rm -rf ~/.cache/huggingface/hub/models--Systran--faster-whisper-*")
            print("  3. Reinstall faster-whisper: pip install --upgrade --force-reinstall faster-whisper")
            raise RuntimeError("Whisper model loading failed")


        self.THRESHOLD = 1000  # Default, adjusted by calibration
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.SILENCE_LIMIT = 1.5 # Seconds of silence to stop recording

        self.calibrate_noise()
        
        # Default keywords (Safety net)
        self.dynamic_keywords = "system, computer, cortana, siri, google, alexa, time, date, exit, stop"

    def update_keywords(self, keywords_str):
        """Updates the command vocabulary prompt for Whisper."""
        self.dynamic_keywords = keywords_str
        print(f"[System] Speech Recognition Vocabulary Updated ({len(keywords_str)} chars).")

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
            self.THRESHOLD = avg_noise * 1.5 # Set threshold 50% above noise floor (increased from 30%)
            # Clamp minimum threshold to avoid super sensitivity
            if self.THRESHOLD < 400: self.THRESHOLD = 400 # Increased from 300
            
            print(f"Calibration Complete. Threshold set to: {self.THRESHOLD:.2f} (Avg Noise: {avg_noise:.2f})")
            
        except Exception as e:
            print(f"Calibration failed: {e}. Using default threshold.")
            self.THRESHOLD = 1000

    def listen(self, timeout=None):
        """
        Records audio until silence and transcribes with Whisper.
        :param timeout: Max time to wait for speech start (seconds). Returns None if timeout.
        """
        try:
            # Check for system speech to prevent self-listening
            if self.is_speaking_flag:
                while self.is_speaking_flag.value:
                    time.sleep(0.1)
            
            with no_alsa_error():
                stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
            
            print("Listening...", end="", flush=True)
            if self.status_queue:
                self.status_queue.put(("LISTENING", None))

            # 1. Wait for speech to start (Voice Activity Detection)
            frames = []
            started = False
            start_time = time.time()
            last_speech_time = time.time()
            
            while True:
                # Check for reset signal
                if self.reset_event and self.reset_event.is_set():
                    return None

                # Timeout Check (Waiting for speech)
                if timeout and not started:
                    if time.time() - start_time > timeout:
                        print("\rListening... (Timeout)        ", end="", flush=True)
                        stream.stop_stream()
                        stream.close()
                        return None
                # Continuous check for system speach (Async interruption)
                if self.is_speaking_flag and self.is_speaking_flag.value:
                    print("\r[System Speaking] Pausing listener...", end="", flush=True)
                    stream.stop_stream()
                    stream.close()
                    
                    # Wait for speech to finish
                    while self.is_speaking_flag.value:
                        time.sleep(0.1)
                    return ""
                
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                # rms = audioop.rms(data, 2) - Replaced for Python 3.13 compatibility
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                rms = np.sqrt(np.mean(samples**2))
                
                if not started:
                    if rms > self.THRESHOLD:
                        started = True
                        print("\rListening... (Speech detected)", end="", flush=True)
                        if self.status_queue:
                             self.status_queue.put(("PROCESSING", None))
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
            # Beam size 1 is faster, but 5 is more accurate. 
            # We use initial_prompt to bias the model towards our command vocabulary.
            # Expanded keywords to prevent "parties to time" hallucinations.
            # keywords = "what is the time, current date, system scan, system cleanup, exit, stop, check ports, firewall, memory, disk, cpu, file manager, create folder, move file, search, hello, greetings, system info"
            
            # Combine dynamic vocab with some static anchors
            # IMPORTANT: Add directional keywords to prevent "left"/"right" being heard as "list"/"write"
            # IMPORTANT: Add common app names for better app launch recognition
            prompt_text = f"Commands: {self.dynamic_keywords}, left, right, up, down, snap left, snap right, move left, move right, window left, window right, WhatsApp, Chrome, Firefox, Notepad, Discord, Spotify, Visual Studio Code, Excel, Word, PowerPoint, system monitor, assistant, open, close, minimize, maximize"
            
            segments, info = self.model.transcribe(
                audio_np, 
                beam_size=5, # Accuracy > Speed
                temperature=0, 
                language="en",
                initial_prompt=prompt_text
            )
            
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
            
            # --- SMART CORRECTIONS FOR COMMON MISRECOGNITIONS ---
            # Fix "snap list" → "snap left" (common Whisper error)
            if "snap list" in full_text:
                full_text = full_text.replace("snap list", "snap left")
                print(f"[Correction] 'snap list' → 'snap left'")
            
            # Fix "move list" → "move left"
            if "move list" in full_text:
                full_text = full_text.replace("move list", "move left")
                print(f"[Correction] 'move list' → 'move left'")
            
            # Fix "window list" → "window left" (if user says "minimize window list")
            # But be careful not to break "list windows"
            if " window list" in full_text or full_text.startswith("window list"):
                full_text = full_text.replace("window list", "window left")
                print(f"[Correction] 'window list' → 'window left'")
            
            # Whitelist/Filter check
            words = full_text.split()
            # Important: Included the security keywords and confirmation words
            important_keywords = [
                "time", "date", "hello", "hi", "hey", "stop", "exit", "bye", "quit", "cortex", "help", 
                "scan", "security", "firewall", "ports", "list", "check", "system",
                "yes", "no", "yeah", "sure", "cancel", "confirm", "deny",
                "open", "close", "launch", "start", "monitor", "sleep", "lock",
                "minimize", "maximize", "restore", "snap", "show", "switch",
                "clipboard", "note", "timer", "create", "delete", "remove", "edit"
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

    def terminate(self):
        """Clean resource release."""
        if self.p:
            self.p.terminate()
            self.p = None

if __name__ == "__main__":
    l = Listener()
    while True:
        l.listen()
