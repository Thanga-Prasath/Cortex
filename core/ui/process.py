import sys
import platform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from .status_window import StatusWindow
# Import Workspace UI components here (runs in UI process)
from components.workspace.ui import WorkspaceEditor, WorkspaceSelector
from components.workspace.manager import WorkspaceManager

def ui_process_target(status_queue, action_queue, reset_event=None, shutdown_event=None):
    """
    Target function for the UI process.
    Initializes QApplication and the StatusWindow.
    """
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Linux/macOS: Prevent dock/taskbar icon from appearing
    if platform.system() != "Windows":
        app.setDesktopFileName("")
    
    # Persistent windows - pass reset and shutdown events to StatusWindow
    window = StatusWindow(reset_event=reset_event, shutdown_event=shutdown_event, action_queue=action_queue)
    window.show()
    
    # Track workspace windows to prevent garbage collection
    workspace_windows = set()
    
    def track_window(win):
        workspace_windows.add(win)
        win.destroyed.connect(lambda: workspace_windows.discard(win))
    
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
                    track_window(editor)
                    
                elif status == "WORKSPACE_SELECTOR":
                    # data = "LAUNCH", "EDIT", or "REMOVE"
                    selector = WorkspaceSelector(manager, data)
                    selector.show()
                    track_window(selector)
                    
                elif status == "LOG":
                    # Forward log to StatusWindow -> HubWindow
                    window.log_activity(data)

                elif status == "SEARCHING":
                    # data = Boolean (True for searching, False for stopped)
                    window.set_searching_state(data)
                    
                    # Also notify any open Cancel Dialog to remove finished searches
                    if isinstance(data, tuple) and not data[1]:
                        query = data[0]
                        from .file_search_gui import CancelSearchDialog
                        for win in list(workspace_windows):
                            if isinstance(win, CancelSearchDialog):
                                win.remove_search(query)
                                
                elif status == "SEARCH_COUNT":
                    # data = Total matches found so far
                    window.update_search_count(data)

                elif status == "FILE_SEARCH_GUI":
                    # data = initial_query
                    from .file_search_gui import FileSearchDialog
                    dlg = FileSearchDialog(initial_query=data, status_window=window)
                    dlg.show()
                    dlg.raise_()
                    dlg.activateWindow()
                    dlg.search_input.setFocus()
                    track_window(dlg)

                elif status == "FILE_SEARCH_RESULTS":
                    # data = (query, unique_results_list)
                    query, results = data
                    from .file_search_gui import FileSearchDialog
                    dlg = FileSearchDialog(initial_query=query, status_window=window)
                    dlg.show_results(results) # Switch to results mode
                    dlg.show()
                    dlg.raise_()
                    dlg.activateWindow()
                    track_window(dlg)

                elif status == "SHOW_CANCEL_DIALOG":
                    # data = list of active search queries
                    active_queries = data
                    from .file_search_gui import CancelSearchDialog
                    dlg = CancelSearchDialog(active_searches=active_queries, action_queue=action_queue, status_window=window)
                    dlg.show()
                    dlg.raise_()
                    dlg.activateWindow()
                    track_window(dlg)

                elif status == "COPY_TO_CLIPBOARD":
                    # data = filepath
                    from PyQt6.QtGui import QPixmap
                    pixmap = QPixmap(data)
                    if not pixmap.isNull():
                        QApplication.clipboard().setPixmap(pixmap)
                        print(f"[UI] Screenshot copied to clipboard: {data}")
                    else:
                        print(f"[UI] Error: Failed to load pixel map for clipboard: {data}")

                elif status == "UPDATE_THEME":
                    window.set_theme(data)

                elif status == "SET_GUI_VISIBLE":
                    window.set_gui_visible(data)

                elif status == "AUTOMATION_LIST":
                    from core.ui.automation_window import AutomationListDialog
                    dlg = AutomationListDialog(parent=None)
                    dlg.show()
                    dlg.raise_()
                    dlg.activateWindow()
                    track_window(dlg)
                    # Keep reference for real-time sync
                    window._active_automation_list_dlg = dlg
                    
                    if action_queue:
                        action_queue.put(("AUTOMATION_DIALOG_STATE", True))
                    
                    def on_dlg_close():
                        setattr(window, '_active_automation_list_dlg', None)
                        if action_queue:
                            action_queue.put(("AUTOMATION_DIALOG_STATE", False))
                            
                    dlg.finished.connect(on_dlg_close)

                elif status == "PRIMARY_UPDATED":
                    dlg = getattr(window, '_active_automation_list_dlg', None)
                    if dlg and dlg.isVisible():
                        dlg.refresh_list()

                else:
                    # Default to status window update
                    window.update_status(status, data)
            except Exception as e:
                print(f"UI Process Error: {e}")
                pass
                
    timer.timeout.connect(check_queue)
    timer.start(30) # Check every 30ms for responsiveness
    
    sys.exit(app.exec())
