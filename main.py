from core.engine import CortexEngine
import multiprocessing
from core.ui.process import ui_process_target

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Create communication queue
    status_queue = multiprocessing.Queue()
    
    # Start UI Process
    ui_process = multiprocessing.Process(target=ui_process_target, args=(status_queue,))
    ui_process.start()
    
    try:
        app = CortexEngine(status_queue)
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        # Clean shutdown
        if 'app' in locals():
            app.shutdown()
        status_queue.put(("EXIT", None))
        ui_process.join()
