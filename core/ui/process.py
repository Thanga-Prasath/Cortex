import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from .status_window import StatusWindow

def ui_process_target(status_queue):
    """
    Target function for the UI process.
    Initializes QApplication and the StatusWindow.
    """
    app = QApplication(sys.argv)
    
    window = StatusWindow()
    window.show()
    
    # Timer to check queue without blocking the UI loop
    timer = QTimer()
    
    def check_queue():
        while not status_queue.empty():
            try:
                status, data = status_queue.get_nowait()
                if status == "EXIT":
                    app.quit()
                    return
                window.update_status(status, data)
            except:
                pass
                
    timer.timeout.connect(check_queue)
    timer.start(100) # Check every 100ms
    
    sys.exit(app.exec())
