
import os
import sys
import time

# Add project root to path
sys.path.append(os.getcwd())

from components.workspace.manager import WorkspaceManager

def test_uwp_close():
    print("Initializing WorkspaceManager...")
    manager = WorkspaceManager()
    
    ws_name = "TestUWPClose"
    # Calculator AppID
    calc_id = "shell:AppsFolder\\Microsoft.WindowsCalculator_8wekyb3d8bbwe!App"
    
    print(f"Defining workspace '{ws_name}' with Calculator...")
    manager.workspaces[ws_name] = [calc_id]
    manager.load_workspaces = lambda: None # Prevent reload
    
    print("Launching workspace...")
    success = manager.launch_workspace(ws_name)
    print(f"Launch Result: {success}")
    
    if success:
        print("Waiting 5 seconds for app to start...")
        time.sleep(5)
        
        print("Closing workspace...")
        manager.close_current_workspace()
        print("Close command executed. Check if Calculator closed.")
    else:
        print("Launch FAILED.")

if __name__ == "__main__":
    test_uwp_close()
