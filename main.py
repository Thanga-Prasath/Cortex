from core.engine import CortexEngine
import multiprocessing
import os
import sys
import platform
from core.ui.process import ui_process_target

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

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Create communication queue
    status_queue = multiprocessing.Queue()
    
    # Create reset and shutdown events
    reset_event = multiprocessing.Event()
    shutdown_event = multiprocessing.Event()
    
    # Start UI Process
    ui_process = multiprocessing.Process(target=ui_process_target, args=(status_queue, reset_event, shutdown_event))
    ui_process.start()
    
    app = None
    result = None
    
    try:
        app = CortexEngine(status_queue, reset_event=reset_event, shutdown_event=shutdown_event)
        result = app.run()
    except KeyboardInterrupt:
        result = "EXIT"
    except Exception as e:
        print(f"[Critical] Main loop error: {e}")
        result = "EXIT"
    
    # --- LOGIC BRANCHING ---
    if result == "RESTART":
        # 1. CLEANUP
        cleanup_system(app, ui_process, status_queue)
        # 2. RESTART
        restart_system()
    else:
        # 1. CLEANUP
        cleanup_system(app, ui_process, status_queue)
        # 2. EXIT
        print("[System] Exiting...")
        sys.stdout.flush()
        # Force clean exit (avoids hanging on threads)
        os._exit(0)
