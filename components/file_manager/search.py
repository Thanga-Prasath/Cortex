import os
import subprocess
from pathlib import Path

def background_search(query, speaker):
    """
    User requested "exact name first, then related files".
    Also requested "provide information of searching location in terminal".
    """
    
    # Windows Implementation
    if os.name == 'nt':
        if speaker:
             speaker.speak(f"Searching for {query}...")
             
        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        desktop = os.path.join(user_profile, 'Desktop')
        documents = os.path.join(user_profile, 'Documents')
        
        search_paths = [
            (desktop, "Desktop"),
            (documents, "Documents"),
            (user_profile, "User Home"),
            ("C:\\", "System Drive"),
            ("D:\\", "D Drive"),
            ("E:\\", "E Drive")
        ]
        
        # Paths to completely ignore to save time
        ignored_dirs = {
            'Windows', 'ProgramData', 'AppData', '$Recycle.Bin', 'System Volume Information',
            'Microsoft', 'Intel', 'PerfLogs'
        }
        
        found_count = 0
        searched_root_paths = set()
        
        for root_path, name in search_paths:
            if not os.path.exists(root_path):
                continue
                
            # Avoid redundant searches (e.g. if Desktop is inside User Home)
            # But here we do simple check: if we already searched a parent of this path?
            # Actually, priority matters. We search Desktop first. If we later search User Home, 
            # we might re-scan Desktop. Optimized way: Exclude previously searched paths?
            # For simplicity and speed in this logic, we keep it simple but be mindful.
            
            # Simple deduplication of roots
            if root_path in searched_root_paths:
                continue
            searched_root_paths.add(root_path)
            
            print(f"[Search] Scanning {name} ({root_path})...")
            
            try:
                # Use os.walk for Windows
                for root, dirs, files in os.walk(root_path):
                    # In-place modification of dirs to prune search
                    dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith('.')]
                    
                    # Check Directories (NEW)
                    for d in dirs:
                        if query.lower() in d.lower():
                            full_path = os.path.join(root, d)
                            
                            # Exact Match Priority
                            if d.lower() == query.lower():
                                print(f"[FOUND DIR] {full_path}")
                                if speaker:
                                    speaker.speak(f"Found folder match for {query}. Opening.")
                                os.startfile(full_path)
                                return

                            # Partial Match
                            if found_count < 3:
                                found_count += 1
                                print(f"[RELATED DIR] {full_path}")
                                if found_count == 1 and speaker:
                                     speaker.speak(f"Found folder {d}. Opening location.")
                                     os.startfile(root) # Open parent to show folder
                                     # or os.startfile(full_path) to enter it? User usually wants to SEE it.
                                     # Let's open the folder itself
                                     os.startfile(full_path)

                    # Check Files
                    for file in files:
                        if query.lower() in file.lower():
                            full_path = os.path.join(root, file)
                            
                            # Exact Match Priority
                            if file.lower() == query.lower():
                                print(f"[FOUND FILE] {full_path}")
                                if speaker:
                                    speaker.speak(f"Found exact file match in {os.path.basename(root)}. Opening.")
                                os.startfile(os.path.dirname(full_path))
                                return

                            # Partial Match
                            if found_count < 3:
                                found_count += 1
                                print(f"[RELATED FILE] {full_path}")
                                if found_count == 1 and speaker:
                                     speaker.speak(f"Found file {file}. Opening location.")
                                     os.startfile(os.path.dirname(full_path))
                                     
                    if found_count >= 3:
                        break
            except Exception as e:
                # Permission errors common in C:\
                pass
                
            if found_count >= 3:
                 break
                 
        if found_count == 0:
             if speaker:
                 speaker.speak(f"Sorry, I couldn't find any files or folders matching {query}.")
        return

    # Linux Implementation (Original)
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
