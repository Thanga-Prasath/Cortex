
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from components.workspace.manager import WorkspaceManager

def test_hybrid_scan():
    print("Initializing WorkspaceManager...")
    manager = WorkspaceManager()
    
    print("Scanning apps...")
    apps = manager.get_system_apps()
    print(f"Total apps found: {len(apps)}")
    
    # Check for UWP
    calc = apps.get("Calculator")
    print(f"Calculator: {calc}")
    
    # Check for Standard App (e.g. Word, Excel, or just a common one like 'WordPad' or 'Paint' or 'Notepad' if in start menu)
    # Note: Notepad might be UWP in Win11, but 'Notepad' classic might exist.
    # Let's check for 'PowerShell' or something likely to be a shortcut.
    
    found_exe = False
    for name, cmd in apps.items():
        if ".exe" in cmd and "shell:AppsFolder" not in cmd:
            print(f"Found Standard App: {name} -> {cmd}")
            found_exe = True
            break
            
    if not found_exe:
        print("WARNING: No standard .exe shortcut found via LNK scan.")
    else:
        print("SUCCESS: Standard .exe shortcuts found.")

    if calc and "shell:AppsFolder" in calc:
        print("SUCCESS: Calculator found as UWP.")
    else:
        print("WARNING: Calculator NOT found or not UWP.")

if __name__ == "__main__":
    test_hybrid_scan()
