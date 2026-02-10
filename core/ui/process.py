import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from .status_window import StatusWindow
# Import Workspace UI components here (runs in UI process)
from components.workspace.ui import WorkspaceEditor, WorkspaceSelector
from components.workspace.manager import WorkspaceManager

def ui_process_target(status_queue, reset_event=None):
    """
    Target function for the UI process.
    Initializes QApplication and the StatusWindow.
    """
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Persistent windows - pass reset_event to StatusWindow
    window = StatusWindow(reset_event=reset_event)
    window.show()
    
    # Track workspace windows to prevent garbage collection
    workspace_windows = []
    
    # Manager for UI process
    manager = WorkspaceManager()

    # Timer to check queue without blocking the UI loop
    timer = QTimer()
    
    def check_queue():
        while not status_queue.empty():
            try:
                msg = status_queue.get_nowait()
                
                # Handle tuple messages
                if isinstance(msg, tuple):
                    status, data = msg
                else:
                    status, data = msg, None

                if status == "EXIT":
                    app.quit()
                    return
                
                elif status == "WORKSPACE_EDITOR":
                    # data = "WorkspaceName" or None
                    editor = WorkspaceEditor(manager, data)
                    editor.show()
                    workspace_windows.append(editor) # Keep reference
                    
                elif status == "WORKSPACE_SELECTOR":
                    # data = "LAUNCH", "EDIT", or "REMOVE"
                    selector = WorkspaceSelector(manager, data)
                    selector.show()
                    workspace_windows.append(selector) # Keep reference

                else:
                    # Default to status window update
                    window.update_status(status, data)
            except Exception as e:
                print(f"UI Process Error: {e}")
                pass
                
    timer.timeout.connect(check_queue)
    timer.start(30) # Check every 30ms for responsiveness
    
    sys.exit(app.exec())
