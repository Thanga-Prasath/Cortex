# ─── PYINSTALLER SAFETY PATCH ────────────────────────────────────────────────
import sys, os
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
if hasattr(sys, '_MEIPASS'):
    os.environ['_MEIPASS2'] = sys._MEIPASS
# ─────────────────────────────────────────────────────────────────────────────

# --- MULTIPROCESSING TARGET WORKAROUNDS ---
def whisper_worker_target(audio_q, result_q, model_size, log_path=""):
    """
    Root-level target for multiprocessing. By placing this at the top of 
    __main__ (main.py) instead of inside core.whisper_subprocess, PyInstaller 
    can flawlessly unpickle the function without triggering a frozen module 
    path corruption error.
    """
    from core.whisper_subprocess import _whisper_worker
    _whisper_worker(audio_q, result_q, model_size, log_path)

# Prevent OpenMP Threading Deadlocks in PyInstaller Temp Environments
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OMP_MAX_ACTIVE_LEVELS"] = "1"

def _log(msg):
    import datetime
    line = f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')}] {msg}"
    print(line, flush=True)

# ─────────────────────────────────────────────────────────────────────────────


_log("TOP: importing multiprocessing...")
import multiprocessing
_log("TOP: importing platform...")
import platform
_log("TOP: importing shutil...")
import shutil

_log("TOP: applying subprocess monkeypatch...")
if platform.system() == "Windows":
    import subprocess as _subprocess

    class _NoconsolesPopen(_subprocess.Popen):
        def __init__(self, *args, **kwargs):
            if "creationflags" not in kwargs:
                kwargs["creationflags"] = _subprocess.CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)

    _subprocess.Popen = _NoconsolesPopen
    import subprocess
    subprocess.Popen = _NoconsolesPopen

_log("TOP: monkeypatch done. importing path_utils...")
from core.utils.path_utils import get_data_path, get_user_data_path
_log("TOP: path_utils imported OK.")


def init_user_data():
    """Copy default configs and data to writable AppData on first run."""
    user_data = get_user_data_path()
    base_data = get_data_path()
    
    files_to_copy = ["user_config.json", "widget_config.json", "workflow.json"]
    for file in files_to_copy:
        src = os.path.join(base_data, file)
        dst = os.path.join(user_data, file)
        if not os.path.exists(dst) and os.path.exists(src):
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                print(f"[Init] Error copying {file}: {e}")
                
    # Also handle automations folder
    auto_src = os.path.join(base_data, "automations")
    auto_dst = os.path.join(user_data, "automations")
    if not os.path.exists(auto_dst) and os.path.exists(auto_src):
        try:
            shutil.copytree(auto_src, auto_dst)
        except Exception as e:
            print(f"[Init] Error copying automations: {e}")


def cleanup_system(app, ui_process, status_queue):
    """Performs a clean shutdown of all components."""
    print("[System] Cleaning up resources...")
    
    # 1. Shutdown Engine (Speaker/Listener)
    if app:
        try:
            app.shutdown()
        except Exception as e:
            print(f"[Warn] Error shutting down engine: {e}")

    # 2. Shutdown UI
    if ui_process and ui_process.is_alive():
        print("[System] Stopping UI...")
        try:
            status_queue.put(("EXIT", None))
            ui_process.join(timeout=2)
            
            if ui_process.is_alive():
                print("[System] Force killing UI process...")
                ui_process.terminate()
                ui_process.join(timeout=1)
        except Exception as e:
            print(f"[Warn] Error killing UI: {e}")

def restart_system():
    """Restarts the application in-place."""
    print("[System] Restarting assistant in-place...")
    
    # --- ROBUST EXECUTABLE FINDER ---
    python_exe = sys.executable
    
    if not os.path.exists(python_exe):
        print(f"[Warn] sys.executable '{python_exe}' not found. Searching for venv...")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if platform.system() == "Windows":
            possible_python = os.path.join(base_dir, "venv", "Scripts", "python.exe")
        else:
            possible_python = os.path.join(base_dir, "venv", "bin", "python")
            
        if os.path.exists(possible_python):
            print(f"[Info] Found venv python: {possible_python}")
            python_exe = possible_python
        else:
            print("[Warn] Venv python not found. Falling back to system 'python'.")
            python_exe = "python"
            
    script = os.path.abspath(__file__)
    args = [python_exe, script]
    
    # --- PLATFORM SPECIFIC RESTART ---
    # Strip PyInstaller multiprocessing _MEIPASS2 so the new process unpacks cleanly
    os.environ.pop('_MEIPASS2', None)

    if platform.system() == "Windows":
        import subprocess
        subprocess.Popen(args)
        sys.stdout.flush()
        os._exit(0)
    else:
        # On Unix-like systems, os.execv replaces the current process.
        # We still flush stdout before execv to ensure messages are printed.
        sys.stdout.flush()
        os.execv(python_exe, args)



def ui_process_target(status_queue, action_queue, reset_event, shutdown_event):
    # This is a placeholder import to avoid circular dependency issues at top level if any
    from core.ui.process import ui_process_target as original_target
    original_target(status_queue, action_queue, reset_event, shutdown_event)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Init user data ONLY in the main process, not in worker processes
    init_user_data()
    
    # [NEW] Set Windows AppUserModelID for Taskbar Grouping natively
    if platform.system() == "Windows":
        import ctypes
        myappid = 'cortex.ai.assistant.1'
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # ── WHISPER MODEL PRE-LOAD (Python mode only) ──────────────────────────────
    # In frozen (PyInstaller) mode ctranslate2 crashes on import even before
    # any child process is spawned — a C++ DLL-load segfault we cannot
    # catch with Python try/except.  Skip pre-loading there and let the
    # Listener handle it in its own background thread (which runs after the
    # greeting, so the user at least sees the app start).
    # In plain `python main.py` mode, pre-loading works perfectly and gives
    # the fastest startup.
    _preloaded_whisper = None

    if not hasattr(sys, '_MEIPASS'):
        _log("Non-frozen mode: pre-loading WhisperModel now...")
        try:
            from faster_whisper import WhisperModel as _WhisperModel
            try:
                _preloaded_whisper = _WhisperModel(
                    "base.en", device="cpu", compute_type="float32",
                    num_workers=1, local_files_only=True
                )
                _log("WhisperModel pre-loaded from cache OK.")
            except Exception as _e1:
                _log(f"Cache miss ({_e1}). Downloading model (~140 MB, once only)...")
                _preloaded_whisper = _WhisperModel(
                    "base.en", device="cpu", compute_type="float32",
                    num_workers=1, local_files_only=False
                )
                _log("WhisperModel downloaded and pre-loaded OK.")
        except Exception as _we:
            import traceback as _tb
            _log(f"[WARN] WhisperModel pre-load failed: {_we}")
            _log(_tb.format_exc())
            _preloaded_whisper = None
    else:
        _log("Frozen mode: skipping ctranslate2 pre-load "
             "(background-thread loader in Listener will handle it after greeting).")
    # ─────────────────────────────────────────────────────────────────────────

    # Create communication queues
    status_queue = multiprocessing.Queue()
    action_queue = multiprocessing.Queue()

    # Create reset and shutdown events
    reset_event = multiprocessing.Event()
    shutdown_event = multiprocessing.Event()

    _log("Queues and Events created.")

    # Spawn UI process AFTER WhisperModel is stable
    _log("Spawning UI process...")
    ui_process = multiprocessing.Process(target=ui_process_target, args=(status_queue, action_queue, reset_event, shutdown_event))
    ui_process.start()
    _log(f"UI process started. PID={ui_process.pid}")

    app = None
    result = None

    try:
        _log("Importing CortexEngine...")
        from core.engine import CortexEngine
        _log("Creating CortexEngine...")
        app = CortexEngine(
            status_queue,
            action_queue=action_queue,
            reset_event=reset_event,
            shutdown_event=shutdown_event,
            whisper_model=_preloaded_whisper   # ← pass pre-loaded model
        )
        _log("CortexEngine created. Starting run loop...")
        result = app.run()
        _log(f"Run loop ended. result={result}")
    except KeyboardInterrupt:
        _log("KeyboardInterrupt received.")
        result = "EXIT"
    except Exception as e:
        import traceback
        _log(f"[CRITICAL EXCEPTION] {e}")
        _log(traceback.format_exc())
        result = "EXIT"

    _log(f"Branching on result: {result}")
    if result == "RESTART":
        cleanup_system(app, ui_process, status_queue)
        restart_system()
    else:
        cleanup_system(app, ui_process, status_queue)
        _log("Exiting via os._exit(0)")
        os._exit(0)



