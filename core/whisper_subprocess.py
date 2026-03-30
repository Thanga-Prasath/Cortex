"""
whisper_subprocess.py — dedicated Whisper transcription subprocess

WHY THIS EXISTS:
  ctranslate2's C++ OpenMP thread pool causes an access violation when
  initialized inside the main process (which already has UI / TTS child
  processes and several Python threads running). Running Whisper in a
  completely isolated subprocess gives it a clean thread environment so
  the model loads without crashing.

DESIGN:
  WhisperProcess spawns a single child process running _whisper_worker().
  The worker loads WhisperModel once, then loops waiting for audio data
  on an input Queue and returning transcription strings on an output Queue.
  The main process sends (audio_np, prompt_text) tuples; receives str.
"""

import multiprocessing
import numpy as np
import sys
import os


# ─── Worker (runs inside the child process) ────────────────────────────────

def _whisper_worker(audio_q: multiprocessing.Queue,
                    result_q: multiprocessing.Queue,
                    model_size: str = "base.en",
                    log_path: str = ""):
    """
    Entry point for the Whisper transcription subprocess.
    Loads the model once, then processes audio in a loop.
    """
    import time
    import traceback
    import datetime
    import os

    def _wlog(msg):
        # We assume standard output is captured or ignored based on environment
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")
        print(f"[{ts}] [WhisperWorker] {msg}", flush=True)

    _wlog(f"Started. PID={os.getpid()}  frozen={getattr(sys, 'frozen', False)}")

    # --- Windows OpenMP and Threading fixes ---
    import os
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    # --- Load the model ---
    model = None
    try:
        _wlog(f"Loading WhisperModel ({model_size})...")
        from faster_whisper import WhisperModel
        try:
            model = WhisperModel(
                model_size, device="cpu", compute_type="float32",
                num_workers=1, local_files_only=True,
                cpu_threads=1,
            )
            _wlog("Model loaded from local cache.")
        except Exception:
            _wlog("Cache miss — downloading model...")
            model = WhisperModel(
                model_size, device="cpu", compute_type="float32",
                num_workers=1, local_files_only=False,
                cpu_threads=1,
            )
            _wlog("Model downloaded and loaded.")

        # Signal success: push a sentinel None to let the parent know
        result_q.put(("READY", None))
        _wlog("Model ready. Entering transcription loop.")

    except Exception as e:
        _wlog(f"[ERROR] Model load failed: {e}\n{traceback.format_exc()}")
        result_q.put(("ERROR", str(e)))
        return  # Exit the subprocess cleanly

    # --- Transcription loop ---
    while True:
        try:
            item = audio_q.get()
            if item is None:
                _wlog("Received shutdown sentinel. Exiting.")
                break

            audio_np, prompt_text = item
            segments, _ = model.transcribe(
                audio_np,
                beam_size=5,
                temperature=0,
                language="en",
                initial_prompt=prompt_text,
            )
            text = "".join(seg.text for seg in segments).strip().lower()
            result_q.put(("TEXT", text))

        except Exception as e:
            _wlog(f"[WARN] Transcription error: {e}")
            result_q.put(("TEXT", ""))


# ─── Client (runs in the main process) ──────────────────────────────────────

class WhisperProcess:
    """
    Manages a dedicated Whisper transcription subprocess.

    Usage:
        wp = WhisperProcess()
        wp.start()          # spawns subprocess + loads model
        text = wp.transcribe(audio_np, prompt)
        wp.stop()
    """

    def __init__(self, model_size: str = "base.en", startup_timeout: int = 180, log_path: str = "", worker_func=None):
        self.model_size = model_size
        self.startup_timeout = startup_timeout
        self.log_path = log_path
        self._audio_q: multiprocessing.Queue = multiprocessing.Queue()
        self._result_q: multiprocessing.Queue = multiprocessing.Queue()
        self._proc: multiprocessing.Process | None = None
        self._ready = False
        
        # Default to internal worker if None passed (like dev testing)
        self._worker_func = worker_func if worker_func is not None else _whisper_worker

    def start(self) -> bool:
        """Spawn the subprocess and wait for it to finish loading the model.
        Returns True on success, False on failure."""
        self._proc = multiprocessing.Process(
            target=self._worker_func,
            args=(self._audio_q, self._result_q, self.model_size, self.log_path),
            daemon=True,
            name="WhisperWorker",
        )
        self._proc.start()

        # Wait for READY / ERROR signal with active polling
        import time
        import queue
        
        start_time = time.time()
        while time.time() - start_time < self.startup_timeout:
            # Check if process unexpectedly died
            if not self._proc.is_alive():
                print("[WhisperProcess] Subprocess died unexpectedly during startup!")
                return False
                
            try:
                # Fast poll
                status, payload = self._result_q.get(timeout=0.1)
                if status == "READY":
                    self._ready = True
                    return True
                else:
                    print(f"[WhisperProcess] Subprocess reported error: {payload}")
                    return False
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[WhisperProcess] Queue error waiting for model: {e}")
                return False
                
        print(f"[WhisperProcess] Timeout waiting {self.startup_timeout}s for model to load.")
        return False

    def transcribe(self, audio_np: np.ndarray, prompt_text: str = "",
                   timeout: int = 60) -> str:
        """Send audio to the subprocess and return the transcription."""
        if not self._ready:
            raise RuntimeError("WhisperProcess not started or failed to load.")
        self._audio_q.put((audio_np, prompt_text))
        try:
            status, payload = self._result_q.get(timeout=timeout)
            if status == "TEXT":
                return payload
        except Exception as e:
            print(f"[WhisperProcess] Timeout waiting for transcription: {e}")
            return ""

    def stop(self):
        """Gracefully shut down the subprocess."""
        if self._proc and self._proc.is_alive():
            try:
                self._audio_q.put(None)   # sentinel
                self._proc.join(timeout=3)
            except Exception:
                pass
            if self._proc.is_alive():
                self._proc.terminate()
        self._ready = False

    @property
    def is_ready(self) -> bool:
        return self._ready and (self._proc is not None) and self._proc.is_alive()
