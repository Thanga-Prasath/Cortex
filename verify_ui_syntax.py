
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    from components.workspace.ui import WorkspaceEditor, WorkspaceSelector
    
    print("Successfully imported UI classes.")
    
    if hasattr(WorkspaceEditor, 'filter_apps'):
        print("WorkspaceEditor has 'filter_apps'.")
    else:
        print("FAIL: WorkspaceEditor missing 'filter_apps'.")
        
    if hasattr(WorkspaceSelector, 'filter_workspaces'):
        print("WorkspaceSelector has 'filter_workspaces'.")
    else:
        print("FAIL: WorkspaceSelector missing 'filter_workspaces'.")
        
except Exception as e:
    print(f"Error: {e}")
