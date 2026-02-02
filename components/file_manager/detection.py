import subprocess
import time
from pathlib import Path

def get_selected_files_from_file_manager():
    """
    Detect files selected in the active file manager window.
    Supports multiple file managers using different detection methods.
    """
    print("[FileManager] Trying detection method 1: qdbus (KDE/Dolphin)")
    # Method 1: Try qdbus for KDE file managers (Dolphin)
    try:
        result = subprocess.run(
            ['qdbus', 'org.kde.dolphin', '/dolphin/Dolphin_1', 'org.kde.dolphin.MainWindow.selectedUrls'],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"[FileManager] qdbus output: {result.stdout.strip()}")
            selected_paths = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith('file://'):
                    from urllib.parse import unquote
                    path_str = unquote(line[7:])
                    path = Path(path_str)
                    if path.exists():
                        selected_paths.append(path)
            if selected_paths:
                print(f"[FileManager] qdbus found {len(selected_paths)} files")
                return selected_paths
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[FileManager] qdbus failed: {e}")
    
    print("[FileManager] Trying detection method 2: gdbus (GNOME/Nautilus)")
    # Method 2: Try gdbus for GNOME file managers (Nautilus)
    try:
        result = subprocess.run(
            ['gdbus', 'call', '--session', '--dest', 'org.gnome.Nautilus',
             '--object-path', '/org/gnome/Nautilus', '--method',
             'org.gnome.Nautilus.FileOperations.GetSelection'],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"[FileManager] gdbus output: {result.stdout.strip()}")
            # Parse gdbus output
            selected_paths = []
            # This is a simplified parser - actual implementation may vary
            for line in result.stdout.strip().split('\n'):
                if 'file://' in line:
                    from urllib.parse import unquote
                    import re
                    urls = re.findall(r'file://[^\s,\'"]+', line)
                    for url in urls:
                        path_str = unquote(url[7:])
                        path = Path(path_str)
                        if path.exists():
                            selected_paths.append(path)
            if selected_paths:
                print(f"[FileManager] gdbus found {len(selected_paths)} files")
                return selected_paths
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[FileManager] gdbus failed: {e}")
    
    print("[FileManager] Trying detection method 3: xclip (clipboard fallback)")
    # Method 3: Fallback to xclip (clipboard method)
    # This method finds the file manager window, focuses it, copies selection, then restores focus
    try:
        # Save current active window
        try:
            active_window_result = subprocess.run(
                ['xdotool', 'getactivewindow'],
                capture_output=True,
                text=True,
                timeout=1
            )
            original_window_id = active_window_result.stdout.strip() if active_window_result.returncode == 0 else None
        except:
            original_window_id = None
        
        # Find file manager window (Nautilus, Thunar, etc.)
        # Use PID-based search as class-based search doesn't work reliably
        file_manager_window = None
        for fm_process in ['nautilus', 'thunar', 'nemo', 'pcmanfm', 'dolphin']:
            try:
                # Get PID of the file manager process
                pid_result = subprocess.run(
                    ['pgrep', fm_process],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                
                if pid_result.returncode == 0 and pid_result.stdout.strip():
                    pids = pid_result.stdout.strip().split('\n')
                    # Try each PID to find windows
                    for pid in pids:
                        try:
                            result = subprocess.run(
                                ['xdotool', 'search', '--pid', pid],
                                capture_output=True,
                                text=True,
                                timeout=1
                            )
                            if result.returncode == 0 and result.stdout.strip():
                                # Get the first window ID
                                file_manager_window = result.stdout.strip().split('\n')[0]
                                print(f"[FileManager] Found {fm_process} window (PID {pid}): {file_manager_window}")
                                break
                        except:
                            continue
                    
                    if file_manager_window:
                        break
            except:
                continue
        
        if not file_manager_window:
            print("[FileManager] No file manager window found")
            # Try to open Nautilus if it's installed
            try:
                print("[FileManager] Attempting to open file manager...")
                subprocess.Popen(['nautilus', str(Path.home())], 
                               stderr=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL)
                time.sleep(1.5)  # Give it time to open
                
                # Try to find it again using PID-based search
                for fm_process in ['nautilus', 'thunar', 'nemo']:
                    try:
                        pid_result = subprocess.run(
                            ['pgrep', fm_process],
                            capture_output=True,
                            text=True,
                            timeout=1
                        )
                        
                        if pid_result.returncode == 0 and pid_result.stdout.strip():
                            pids = pid_result.stdout.strip().split('\n')
                            for pid in pids:
                                try:
                                    result = subprocess.run(
                                        ['xdotool', 'search', '--pid', pid],
                                        capture_output=True,
                                        text=True,
                                        timeout=1
                                    )
                                    if result.returncode == 0 and result.stdout.strip():
                                        file_manager_window = result.stdout.strip().split('\n')[0]
                                        print(f"[FileManager] Opened and found {fm_process} window (PID {pid}): {file_manager_window}")
                                        break
                                except:
                                    continue
                            
                            if file_manager_window:
                                break
                    except:
                        continue
                
                if not file_manager_window:
                    print("[FileManager] Could not find file manager window even after opening")
                    return []
            except:
                print("[FileManager] Could not open file manager automatically")
                return []
        
        # Focus the file manager window
        subprocess.run(
            ['xdotool', 'windowactivate', file_manager_window],
            check=False,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            timeout=0.5
        )
        time.sleep(0.2)  # Give it time to focus
        
        # Simulate Ctrl+C on the file manager window
        subprocess.run(
            ['xdotool', 'key', 'ctrl+c'],
            check=False,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            timeout=0.5
        )
        time.sleep(0.15)
        
        # Restore original window focus
        if original_window_id:
            subprocess.run(
                ['xdotool', 'windowactivate', original_window_id],
                check=False,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                timeout=0.5
            )
        
        # Read clipboard
        result = subprocess.run(
            ['xclip', '-selection', 'clipboard', '-o'],
            capture_output=True,
            text=True,
            timeout=1
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"[FileManager] Clipboard content: {result.stdout.strip()[:200]}")
            selected_paths = []
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line.startswith('file://'):
                    from urllib.parse import unquote
                    path_str = unquote(line[7:])
                    path = Path(path_str)
                    if path.exists():
                        selected_paths.append(path)
                elif line.startswith('/'):
                    path = Path(line)
                    if path.exists():
                        selected_paths.append(path)
            if selected_paths:
                print(f"[FileManager] xclip found {len(selected_paths)} files")
                return selected_paths
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[FileManager] xclip failed: {e}")
    
    print("[FileManager] All detection methods failed")
    return []
