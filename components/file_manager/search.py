import os
import subprocess
from pathlib import Path

def background_search(query, speaker):
    """
    User requested "exact name first, then related files".
    Also requested "provide information of searching location in terminal".
    """
    
    user_home = str(Path.home())
    search_zones = [
        (user_home, "User Home"),
        ('/media', "External Media"),
        ('/mnt', "Mounts"),
        ('/', "System Root")
    ]
    
    # Filter existing zones
    valid_zones = []
    for path, name in search_zones:
        if os.path.exists(path):
            valid_zones.append((path, name))
            
    # Zones to exclude when searching root to avoid duplicates/double-work
    priority_paths = [z[0] for z in valid_zones if z[0] != '/']
    
    seen_paths = set()
    max_windows = 5
    windows_opened = 0
    
    if speaker:
        speaker.speak(f"Started searching for exact match of {query}...")
    
    # --- Phase 1: Exact Match ---
    for zone_path, zone_name in valid_zones:
        if windows_opened >= max_windows:
             break
        
        print(f"\n[Search] Scanning {zone_name} ({zone_path}) for exact matches of '{query}'...")
        
        try:
            # Construct command
            cmd = ['find', zone_path]
            
            # Exclusions
            excludes = []
            
            # Standard System Excludes
            sys_excludes = ['/proc', '/sys', '/dev', '/run', '/tmp', '/snap']
            
            # If we are searching Root, also exclude the Priority Paths we just searched
            if zone_path == '/':
                 excludes.extend(sys_excludes)
                 # Add priority paths to excludes
                 excludes.extend(priority_paths)
            
            # Build Exclude Args
            exclude_args = []
            if excludes:
                # -path /proc -prune -o -path /sys -prune -o ...
                exclude_args.append('(')
                for i, ex in enumerate(excludes):
                    exclude_args.extend(['-path', ex, '-prune'])
                    if i < len(excludes) - 1:
                        exclude_args.append('-o')
                exclude_args.append(')')
                exclude_args.append('-o') # Continue with search if not pruned
            
            cmd.extend(exclude_args)
            
            # Search Arguments
            # -name "query" -print
            cmd.extend(['-name', query, '-print'])
            
            # Run find
            # We use Popen to process line by line
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                
                path = line.strip()
                if path and path not in seen_paths:
                    seen_paths.add(path)
                    print(f"[FOUND] {path}")
                    
                    if windows_opened < max_windows:
                        # Open the parent folder
                        parent_dir = os.path.dirname(path)
                        if speaker:
                            speaker.speak(f"Found {query} in {os.path.basename(parent_dir)}. Opening location.")
                        
                        subprocess.Popen(['xdg-open', parent_dir], stderr=subprocess.DEVNULL)
                        windows_opened += 1
                        
                        if windows_opened >= max_windows:
                            process.terminate()
                            break
            
            process.wait()

        except Exception as e:
            print(f"Error searching {zone_name}: {e}")

    # --- Phase 2: Related/Partial Match ---
    if windows_opened == 0:
        if speaker:
            speaker.speak(f"No exact matches found. Searching for related files...")
        
        for zone_path, zone_name in valid_zones:
            if windows_opened >= max_windows:
                 break

            print(f"\n[Search] Scanning {zone_name} ({zone_path}) for related matches...")
            
            try:
                cmd = ['find', zone_path]
                
                excludes = []
                sys_excludes = ['/proc', '/sys', '/dev', '/run', '/tmp', '/snap']
                if zone_path == '/':
                     excludes.extend(sys_excludes)
                     excludes.extend(priority_paths)
                
                exclude_args = []
                if excludes:
                    exclude_args.append('(')
                    for i, ex in enumerate(excludes):
                        exclude_args.extend(['-path', ex, '-prune'])
                        if i < len(excludes) - 1:
                            exclude_args.append('-o')
                    exclude_args.append(')')
                    exclude_args.append('-o')

                cmd.extend(exclude_args)
                
                # Case insensitive partial match: -iname "*query*"
                cmd.extend(['-iname', f'*{query}*', '-print'])
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    
                    path = line.strip()
                    if path and path not in seen_paths:
                        seen_paths.add(path)
                        print(f"[RELATED] {path}")
                        
                        if windows_opened < max_windows:
                            parent_dir = os.path.dirname(path)
                            if speaker:
                                speaker.speak(f"Found related item in {os.path.basename(parent_dir)}. Opening.")
                            
                            subprocess.Popen(['xdg-open', parent_dir], stderr=subprocess.DEVNULL)
                            windows_opened += 1
                            
                            if windows_opened >= max_windows:
                                process.terminate()
                                break
                process.wait()

            except Exception as e:
                 print(f"Error searching {zone_name}: {e}")

    if windows_opened == 0:
        if speaker:
            speaker.speak(f"Sorry, I couldn't find any files matching {query}.")
    else:
        print("[Search] Search completed.")
