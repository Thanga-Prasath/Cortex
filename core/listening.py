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
    def __init__(self, status_queue=None, is_speaking_flag=None, reset_event=None,
                 shutdown_event=None, preloaded_model=None):
        self.status_queue = status_queue
        self.is_speaking_flag = is_speaking_flag
        self.reset_event = reset_event
        self.shutdown_event = shutdown_event
        self.model_size = "base.en"
        self.model = None          # set when using in-process model
        self._whisper_proc = None  # set when using subprocess model

        self.THRESHOLD = 1000
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.SILENCE_LIMIT = 1.2

        # Default keywords (Safety net)
        self.dynamic_keywords = "system, computer, cortana, siri, google, alexa, time, date, exit, stop"

        # Event to signal when either path is ready
        self._model_ready = threading.Event()

        # Start PyAudio (lightweight — no C++ thread pool)
        try:
            self.p = pyaudio.PyAudio()
        except Exception as e:
            print(f"[Listener] PyAudio init error: {e}")

        # Calibrate noise (doesn't need Whisper)
        self.calibrate_noise()

        if preloaded_model is not None:
            # ── Fast path: Python mode — model pre-loaded in main() before
            # any child processes were spawned, passed directly here.
            self.model = preloaded_model
            self._model_ready.set()
            print("[✓] Whisper Model received from pre-loader.")

        elif getattr(__import__('sys'), 'frozen', False):
            # ── Frozen (PyInstaller) mode: ctranslate2 causes an access
            # violation when loaded in a thread of this process (because the
            # main process already has 4+ competing threads from the UI/TTS
            # subprocesses and the audio monitor).
            # Fix: spawn a dedicated subprocess with a clean thread state.
            import threading as _th
            _th.Thread(target=self._start_whisper_subprocess, daemon=True).start()

        else:
            # ── Python dev-mode fallback: background thread (preloaded_model
            # should always be set in this path, but keep as safety net).
            import threading as _th
            _th.Thread(target=self._load_model_inprocess, daemon=True).start()

    # ── Subprocess path (frozen / PyInstaller) ─────────────────────────────

    def _start_whisper_subprocess(self):
        """Spawn a dedicated Whisper process.  Called from a short-lived thread
        so __init__ returns immediately and the greeting can be spoken."""
        try:
            from __main__ import _log
            def _tlog(m): _log(f"[WhisperSubproc] {m}")
        except Exception:
            def _tlog(m): print(f"[WhisperSubproc] {m}", flush=True)

        try:
            from .whisper_subprocess import WhisperProcess
            _tlog("Spawning Whisper subprocess...")
            
            # Resolve the target function aggressively from the root __main__ 
            # to survive PyInstaller's multiprocessing unpickling bugs
            try:
                from __main__ import whisper_worker_target
            except ImportError:
                # Fallback for when running listening.py directly in tests
                from .whisper_subprocess import _whisper_worker as whisper_worker_target

            wp = WhisperProcess(model_size=self.model_size, startup_timeout=180, worker_func=whisper_worker_target)
            ok = wp.start()
            if ok:
                self._whisper_proc = wp
                _tlog("Whisper subprocess ready.")
            else:
                _tlog("[ERROR] Whisper subprocess failed to start.")
        except Exception as e:
            import traceback
            _tlog(f"[ERROR] {e}\n{traceback.format_exc()}")

        finally:
            self._model_ready.set()  # always unblock waiters

    # ── In-process path (Python / dev mode) ───────────────────────────────

    def _load_model_inprocess(self):
        """Background thread: load WhisperModel directly (Python mode only)."""
        try:
            from __main__ import _log
            def _tlog(m): _log(f"[BG-Whisper] {m}")
        except Exception:
            def _tlog(m): print(f"[BG-Whisper] {m}", flush=True)

        try:
            _tlog(f"Loading WhisperModel ({self.model_size})...")
            try:
                self.model = WhisperModel(
                    self.model_size, device="cpu", compute_type="float32",
                    num_workers=1, local_files_only=True, cpu_threads=1,
                )
                _tlog("Local cache found OK.")
            except Exception as _e1:
                _tlog(f"Cache miss ({_e1}). Downloading...")
                self.model = WhisperModel(
                    self.model_size, device="cpu", compute_type="float32",
                    num_workers=1, local_files_only=False, cpu_threads=1,
                )
            _tlog("WhisperModel loaded.")
        except Exception as e:
            import traceback
            _tlog(f"[ERROR] {e}\n{traceback.format_exc()}")
            self.model = None
        finally:
            self._model_ready.set()

    # ── Shared transcription interface ────────────────────────────────────

    def _ensure_model(self, timeout=180):
        """Block until Whisper (subprocess or in-process) is ready."""
        if not self._model_ready.wait(timeout=timeout):
            print("[Listener] WARNING: Whisper did not load within timeout!")
        if self._whisper_proc is None and self.model is None:
            raise RuntimeError("Whisper model / subprocess failed to start. Cannot transcribe.")

    def _transcribe(self, audio_np, prompt_text):
        """Route to subprocess or in-process model and return (segments, info)."""
        self._ensure_model()
        if self._whisper_proc and self._whisper_proc.is_ready:
            # Subprocess path: returns a plain string
            text = self._whisper_proc.transcribe(audio_np, prompt_text)
            # Wrap in an iterable of fake segments so callers work unchanged
            class _Seg:
                def __init__(self, t): self.text = t
            class _Info: pass
            return [_Seg(text)], _Info()
        else:
            # In-process path: direct WhisperModel call
            return self.model.transcribe(
                audio_np, beam_size=5, temperature=0,
                language="en", initial_prompt=prompt_text,
            )


    def update_keywords(self, keywords_str):
        """Updates the command vocabulary prompt for Whisper."""
        self.dynamic_keywords = keywords_str
        print(f"[System] Speech Recognition Vocabulary Updated ({len(keywords_str)} chars).")

    def _get_input_stream_kwargs(self):
        """Returns keyword arguments for opening the PyAudio stream. 
        Omitting 'input_device_index' forces PyAudio to use the OS Default via Sound Mapper."""
        return {
            'format': self.FORMAT,
            'channels': self.CHANNELS,
            'rate': self.RATE,
            'input': True,
            'frames_per_buffer': self.CHUNK
        }

    def calibrate_noise(self):
        """Measures ambient noise level to set dynamic threshold."""
        print("Calibrating background noise... (Please stay quiet)")
        try:
            kwargs = self._get_input_stream_kwargs()
            with no_alsa_error():
                try:
                    stream = self.p.open(**kwargs)
                except Exception as e:
                    if "-9999" in str(e):
                        # PortAudio instance is corrupted by a hot-swap. Recreate entirely.
                        self.p.terminate()
                        self.p = pyaudio.PyAudio()
                    else:
                        print(f"[!] Target input device unavailable, fallback to default: {e}")
                        
                    if 'input_device_index' in kwargs:
                        del kwargs['input_device_index']
                        
                    try:
                        stream = self.p.open(**kwargs)
                    except Exception as fallback_e:
                        if "-9999" in str(fallback_e):
                            # Ultimate fallback: PyAudio is completely dead, reboot it
                            self.p.terminate()
                            self.p = pyaudio.PyAudio()
                        return
            
            stream.start_stream()
            
            # Discard initial "pop" chunks
            for _ in range(5):
                stream.read(self.CHUNK, exception_on_overflow=False)

            noise_levels = []
            for _ in range(30): # Listen for ~1.5 second
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                # rms = audioop.rms(data, 2) - Replaced for Python 3.13 compatibility
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                # Subtract mean to remove DC offset before calculating RMS
                samples = samples - np.mean(samples)
                rms = np.sqrt(np.mean(samples**2))
                noise_levels.append(rms)
            
            stream.stop_stream()
            stream.close()
            
            avg_noise = np.mean(noise_levels)
            self.THRESHOLD = avg_noise * 1.5 # Set threshold 50% above noise floor
            # Clamp minimum threshold to avoid super sensitivity
            if self.THRESHOLD < 400: self.THRESHOLD = 400 # Increased from 300
            
            print(f"Calibration Complete. Threshold set to: {self.THRESHOLD:.2f} (Avg Noise: {avg_noise:.2f})")
            
        except Exception as e:
            print(f"Calibration failed: {e}. Using default threshold.")
            self.THRESHOLD = 1000

    def listen(self, timeout=None, is_on_hold=False):
        """
        Records audio until silence and transcribes with Whisper.
        :param timeout: Max time to wait for speech start (seconds). Returns None if timeout.
        :param is_on_hold: If True, publishes IDLE status instead of LISTENING.
        """
        try:
            # Check for system speech to prevent self-listening
            # Check for system speech to prevent self-listening
            if self.is_speaking_flag:
                wait_start = time.time()
                while self.is_speaking_flag.value:
                    time.sleep(0.1)
                    # Safety: If we've been "speaking" for > 30s, force-reset it 
                    # This prevents hangs if the TTS process dies unexpectedly.
                    if time.time() - wait_start > 30:
                        print("\r[System Warning] Speaking flag stuck. Force resetting listener...")
                        self.is_speaking_flag.value = False
                        break
            
            kwargs = self._get_input_stream_kwargs()
            with no_alsa_error():
                try:
                    stream = self.p.open(**kwargs)
                except Exception as e:
                    if "-9999" in str(e):
                        # PortAudio routing graph broken by hot-swap. Re-initialize natively.
                        self.p.terminate()
                        self.p = pyaudio.PyAudio()
                        time.sleep(1) # Let COM objects settle
                    else:
                        print(f"[!] Target input device unavailable, fallback to default: {e}")
                        
                    if 'input_device_index' in kwargs:
                        del kwargs['input_device_index']
                        
                    try:
                        stream = self.p.open(**kwargs)
                    except Exception as fallback_e:
                        if "-9999" in str(fallback_e):
                            self.p.terminate()
                            self.p = pyaudio.PyAudio()
                            time.sleep(1)
                        return ""
            
            print("Listening...", end="", flush=True)
            if self.status_queue:
                if is_on_hold:
                    self.status_queue.put(("IDLE", None))
                else:
                    self.status_queue.put(("LISTENING", None))

            # 1. Wait for speech to start (Voice Activity Detection)
            frames = []
            started = False
            start_time = time.time()
            last_speech_time = time.time()
            
            while True:
                # Check for reset or shutdown signal
                if self.reset_event and self.reset_event.is_set():
                    return None
                if self.shutdown_event and self.shutdown_event.is_set():
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
                # Subtract mean to remove DC offset
                samples = samples - np.mean(samples)
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
            
            segments, info = self._transcribe(audio_np, prompt_text)
            
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
                "clipboard", "note", "timer", "create", "delete", "remove", "edit",
                "restart", "reboot", "shutdown", "hibernate",
                "calculator", "clock", "cls", "cut", "day", "dir", "dxdiag", "goodbye", 
                "gpedit", "greetings", "hour", "icy", "kill", "ls", "month", "move", 
                "mspaint", "notepad", "paint", "paste", "perfmon", "play", "powershell", 
                "preferences", "resmon", "run", "screenshot", "snapshot", "speedtest", 
                "terminate", "today", "top", "tree", "unmaximize", "uptime", "winver", "year"
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
        except OSError as e:
            if "-9999" in str(e):
                # Silently catch PyAudio stream disconnection and reset
                pass
            else:
                print(f"\n[System] Audio stream error: {e}")
            return ""
        except Exception as e:
            print(f"\nError in listening: {e}")
            return ""
        finally:
            try:
                if 'stream' in locals() and stream.is_active():
                    stream.stop_stream()
                    stream.close()
            except: pass

    def listen_for_interrupt(self, timeout=30):
        """
        A SEPARATE lightweight listener used exclusively by the interrupt thread.
        KEY DIFFERENCES from listen():
          - Opens its OWN PyAudio instance so it doesn't conflict with self.p
          - Does NOT wait for is_speaking_flag (that's exactly the point)
          - Hard timeout so it doesn't block forever
          - Only transcribes short bursts, not full commands
        Returns the transcript string, or empty string on timeout/no speech.
        """
        p_int = None
        stream_int = None
        try:
            with no_alsa_error():
                p_int = pyaudio.PyAudio()
                try:
                    stream_int = p_int.open(
                        format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK
                    )
                except Exception as e:
                    print(f"[Interrupt Listener] Could not open audio stream: {e}")
                    return ""

            frames = []
            started = False
            start_time = time.time()
            last_speech_time = time.time()

            while True:
                # Global hard timeout
                if time.time() - start_time > timeout:
                    break

                # If speaking already finished with no speech detected, bail out
                if not started and self.is_speaking_flag and not self.is_speaking_flag.value:
                    # Speaking ended; no point listening further
                    if time.time() - start_time > 1.0:  # Give at least 1s
                        break

                try:
                    data = stream_int.read(self.CHUNK, exception_on_overflow=False)
                except Exception:
                    break

                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                samples = samples - np.mean(samples)
                rms = np.sqrt(np.mean(samples**2))

                if not started:
                    if rms > self.THRESHOLD:
                        started = True
                        frames.append(data)
                        last_speech_time = time.time()
                else:
                    frames.append(data)
                    if rms > self.THRESHOLD:
                        last_speech_time = time.time()
                    # Silence = done speaking
                    if time.time() - last_speech_time > 0.8:
                        break
                    # Hard cap: 5 seconds max for an interrupt phrase
                    if len(frames) * self.CHUNK / self.RATE > 5:
                        break

            if not frames:
                return ""

            # Transcribe captured audio
            audio_data = b''.join(frames)
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = self.model.transcribe(
                audio_np,
                beam_size=1,        # Fast — we only need coarse recognition
                temperature=0,
                language="en",
                initial_prompt="stop talking, stop speaking, be quiet, shut up, enough, silence, quiet"
            )
            text = "".join(seg.text for seg in segments).strip().lower()
            text = text.replace(".", "").replace("?", "").replace(",", "").replace("!", "")
            return text

        except Exception as e:
            print(f"[Interrupt Listener] Error: {e}")
            return ""
        finally:
            try:
                if stream_int and stream_int.is_active():
                    stream_int.stop_stream()
                    stream_int.close()
            except: pass
            try:
                if p_int:
                    p_int.terminate()
            except: pass

    def terminate(self):
        """Clean resource release."""
        if self.p:
            self.p.terminate()
            self.p = None

if __name__ == "__main__":
    l = Listener()
    while True:
        l.listen()
