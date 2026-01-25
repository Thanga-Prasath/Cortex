import os
import shutil
import subprocess
import pathlib
import json
import threading
from pathlib import Path

class FileManagerEngine:
    def __init__(self, speaker):
        self.speaker = speaker
        self.desktop_path = Path.home() / "Desktop"
        self.selected_items = []

    def _get_active_window_hyprland(self):
        """
        Get active window title using hyprctl (for Hyprland).
        """
        try:
            output = subprocess.check_output(['hyprctl', 'activewindow', '-j'], stderr=subprocess.DEVNULL)
            window_info = json.loads(output.decode('utf-8'))
            return window_info.get('title', None)
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            pass
        return None

    def _get_active_window_title(self):
        """
        Get the active window title trying multiple methods:
        1. hyprctl (Hyprland)
        2. xprop (X11 / XWayland)
        """
        # Try Hyprland first
        title = self._get_active_window_hyprland()
        if title:
            return title

        # Fallback to xprop
        try:
            # 1. Get the active window ID
            root_check = subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stderr=subprocess.DEVNULL)
            # Output format: _NET_ACTIVE_WINDOW(WINDOW): window id # 0x1234567
            root_str = root_check.decode('utf-8').strip()
            
            if 'window id #' not in root_str:
                return None
            
            window_id = root_str.split('window id #')[-1].strip()
            
            # 2. Get the window name for that ID
            name_check = subprocess.check_output(['xprop', '-id', window_id, '_NET_WM_NAME'], stderr=subprocess.DEVNULL)
            # Output format: _NET_WM_NAME(UTF8_STRING) = "Title"
            name_str = name_check.decode('utf-8').strip()
            
            if '=' not in name_str:
                # Try WM_NAME as fallback
                name_check = subprocess.check_output(['xprop', '-id', window_id, 'WM_NAME'], stderr=subprocess.DEVNULL)
                name_str = name_check.decode('utf-8').strip()
            
            if '"' in name_str:
                # Extract content inside quotes
                # Using simple split might fail if title has quotes, but good enough for now
                # Usually it's at the end: ... = "Title"
                title = name_str.split('=', 1)[1].strip().strip('"')
                return title
                
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            pass
            
        return None

    def _get_active_location(self):
        """
        Attempts to get the path from the active window title.
        Defaults to Desktop if unsuccessful.
        """
        try:
            window_title = self._get_active_window_title()
            
            if not window_title:
                return self.desktop_path
            
            print(f"[FileManager] Active window: {window_title}")
            
            # Heuristics to extract path from title
            # Many file managers format title as: "Folder Name — App Name" or "Folder Name" or "/full/path"
            
            # 1. Check if the full title is a path
            if os.path.exists(window_title) and os.path.isdir(window_title):
                return Path(window_title)
            
            # 2. Split by common separators to get the folder name
            separators = [" — ", " - ", " : ", " at "] # " — " is common in KDE/Gnome
            
            potential_names = [window_title]
            for sep in separators:
                if sep in window_title:
                    potential_names.extend(window_title.split(sep))
            
            # Prioritize the first part (usually the folder name)
            for name in potential_names:
                name = name.strip()
                if not name:
                    continue
                
                # Check 2a: Is it an absolute path?
                if name.startswith("/") and os.path.isdir(name):
                    return Path(name)
                    
                # Check 2b: Is it in Home?
                home_path = Path.home() / name
                if home_path.is_dir():
                    return home_path
                    
                # Check 2c: Is it in Desktop?
                desktop_path = self.desktop_path / name
                if desktop_path.is_dir():
                    return desktop_path
                    
                # Check 2d: Is it "Home" or user name?
                if name.lower() in ["home", os.getlogin(), "file manager", "files"]:
                    return Path.home()

        except Exception as e:
            print(f"[FileManager] Error identifying location: {e}")
            
        return self.desktop_path

    def _extract_name(self, command, keywords):
        """
        Extracts the target name from the command.
        """
        for kw in keywords:
            if kw in command:
                parts = command.split(kw)
                if len(parts) > 1:
                    return parts[1].strip()
        
        # Fallback: create default name if not found? 
        # Or return last word
        return command.split()[-1]

    def _create_item(self, is_folder, command):
        location = self._get_active_location()
        
        keywords = ["named", "called", "folder", "file", "directory"]
        name = self._extract_name(command, keywords)
        
        # Clean up name (remove quotes if user said "create folder 'foo'")
        name = name.replace("'", "").replace('"', "")
        
        target_path = location / name
        
        try:
            if is_folder:
                target_path.mkdir(parents=True, exist_ok=True)
                self.speaker.speak(f"Created folder {name} in {location.name}.")
            else:
                target_path.touch(exist_ok=True)
                self.speaker.speak(f"Created file {name} in {location.name}.")
        except Exception as e:
            self.speaker.speak(f"I encountered an error creating the item: {str(e)}")

    def _move_item(self, command):
        # Case 1: "Move [source] to [dest]"
        if " to " in command:
            parts = command.split(" to ")
            source_raw = parts[0].replace("move file", "").replace("move folder", "").replace("move", "").strip()
            dest_raw = parts[1].strip()
            
            # Clean paths
            source_raw = source_raw.replace("'", "").replace('"', "")
            dest_raw = dest_raw.replace("'", "").replace('"', "")

            # Resolve Source
            active_loc = self._get_active_location()
            possible_sources = [
                active_loc / source_raw,
                self.desktop_path / source_raw,
                Path.home() / source_raw
            ]
            
            source_path = None
            for p in possible_sources:
                if p.exists():
                    source_path = p
                    break
            
            if not source_path:
                self.speaker.speak(f"I could not find the file or folder named {source_raw}.")
                return

            # Resolve Destination
            standard_folders = ["Documents", "Downloads", "Music", "Pictures", "Videos", "Desktop"]
            dest_path = None
            
            for std in standard_folders:
                if dest_raw.lower() in std.lower():
                    dest_path = Path.home() / std
                    break
            
            if not dest_path:
                 p = Path.home() / dest_raw
                 if p.is_dir():
                     dest_path = p
            
            if not dest_path:
                 self.speaker.speak(f"I assume you want to move it to {dest_raw}, but I cannot find that folder.")
                 return

            try:
                shutil.move(str(source_path), str(dest_path))
                self.speaker.speak(f"Moved {source_raw} to {dest_path.name}.")
            except Exception as e:
                self.speaker.speak(f"I could not move the file: {str(e)}")
            return

        # Case 2: "Move [source]" or just "Move" (Stateful)
        cleaned_cmd = command.lower().replace("move file", "").replace("move folder", "").replace("move items", "").replace("move", "").strip()
        cleaned_cmd = cleaned_cmd.replace("'", "").replace('"', "")

        # Subcase 2a: Just "Move" (User wants to move already selected items)
        if not cleaned_cmd:
            if self.selected_items:
                self.speaker.speak(f"Ready to move {len(self.selected_items)} items. Please navigate to the destination folder and say 'move here'.")
            else:
                 self.speaker.speak("No files selected. Please select the file you want to move first.")
            return

        # Subcase 2b: "Move [filename]" (User wants to pick a file to move)
        source_raw = cleaned_cmd
        active_loc = self._get_active_location()
        
        possible_sources = [
            active_loc / source_raw,
            self.desktop_path / source_raw,
            Path.home() / source_raw
        ]
        
        source_path = None
        for p in possible_sources:
            if p.exists():
                source_path = p
                break
        
        if source_path:
             self.selected_items.append(source_path)
             self.speaker.speak(f"Added {source_raw} to move list. Please navigate to the destination folder and say 'move here'.")
        else:
             self.speaker.speak(f"I could not find {source_raw} to move.")

    def _select_item(self, command):
        location = self._get_active_location()
        
        keywords = ["select file", "select folder", "pick file", "choose file", "select", "pick", "grab"]
        name = self._extract_name(command, keywords)
        name = name.replace("'", "").replace('"', "")
        
        target = location / name
        if not target.exists():
            # Try partial match logic if exact match fail?
            # For now strict
            self.speaker.speak(f"I cannot find {name} in {location.name}.")
            return
            
        self.selected_items.append(target)
        self.speaker.speak(f"Selected {name}. Now please navigate to the destination folder and say 'move here'.")

    def _move_selected_here(self, command):
        if not self.selected_items:
            self.speaker.speak("You haven't selected any files to move.")
            return

        dest_location = self._get_active_location()
        
        success_count = 0
        for item in self.selected_items:
            try:
                # Handle name collision by appending _copy or similar?
                # For now simple overwrite protection is done by shutil.move but it might fail or overwrite
                # Let's just move
                
                # Check if dest == source (no op)
                if item.parent == dest_location:
                    continue
                    
                destination = dest_location / item.name
                shutil.move(str(item), str(destination))
                success_count += 1
            except Exception as e:
                print(f"Error moving {item}: {e}")
        
        self.selected_items = [] # Clear selection
        if success_count > 0:
            self.speaker.speak(f"Moved {success_count} items to {dest_location.name}.")
        else:
            self.speaker.speak("Could not move items.")

    def _background_search(self, query):
        # User requested "exact name first, then related files".
        # Also requested "provide information of searching location in terminal".
        # We will split the search into priority zones.
        
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
        # We exclude /home, /media, /mnt from the "/" search if they were already searched.
        # But specifically, we must exclude the specific paths we added.
        priority_paths = [z[0] for z in valid_zones if z[0] != '/']
        
        seen_paths = set()
        max_windows = 5
        windows_opened = 0
        
        self.speaker.speak(f"Started searching for exact match of {query}...")
        
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
                
                # Standard System Excludes (Always prune these to avoid recursion/errors)
                sys_excludes = ['/proc', '/sys', '/dev', '/run', '/tmp', '/snap']
                
                # If we are searching Root, also exclude the Priority Paths we just searched
                if zone_path == '/':
                     excludes.extend(sys_excludes)
                     # Add priority paths to excludes
                     excludes.extend(priority_paths)
                else:
                    # If inside Home or Media, we usually don't need to prune system dirs, 
                    # but safety first if there are symlinks? 'find' handles symlinks depending on flags.
                    # defaults usually don't follow symlinks to dirs unless specified.
                    pass
                
                # Build prune list for find
                if excludes:
                    # ( -path /proc -o -path /sys ... ) -prune -o
                    cmd.append('(')
                    for i, excl in enumerate(excludes):
                        cmd.extend(['-path', excl])
                        if i < len(excludes) - 1:
                            cmd.append('-o')
                    cmd.extend([')', '-prune', '-o'])
                
                # Match logic
                cmd.extend(['-iname', f'{query}', '-print'])
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                
                for line in process.stdout:
                    found_path = line.strip()
                    if found_path and found_path not in seen_paths:
                        print(f"  [Found] {found_path}")
                        self.speaker.speak(f"Found exact match: {os.path.basename(found_path)}.")
                        
                        target_dir = found_path
                        if os.path.isfile(found_path):
                            target_dir = os.path.dirname(found_path)
                            
                        subprocess.Popen(['xdg-open', target_dir], stderr=subprocess.DEVNULL)
                        seen_paths.add(found_path)
                        windows_opened += 1
                        
                        if windows_opened >= max_windows:
                            self.speaker.speak("Limit of opened windows reached.")
                            process.terminate()
                            break
            except Exception as e:
                print(f"[Error] Search failed in {zone_name}: {e}")

        # --- Phase 2: Partial Match ---
        if windows_opened < max_windows:
            self.speaker.speak(f"Looking for related files...")
            
            for zone_path, zone_name in valid_zones:
                if windows_opened >= max_windows:
                    break
                
                print(f"[Search] Scanning {zone_name} ({zone_path}) for related files...")
                
                try:
                    cmd = ['find', zone_path]
                    
                    excludes = []
                    sys_excludes = ['/proc', '/sys', '/dev', '/run', '/tmp', '/snap']
                    
                    if zone_path == '/':
                         excludes.extend(sys_excludes)
                         excludes.extend(priority_paths)
                    
                    if excludes:
                        cmd.append('(')
                        for i, excl in enumerate(excludes):
                            cmd.extend(['-path', excl])
                            if i < len(excludes) - 1:
                                cmd.append('-o')
                        cmd.extend([')', '-prune', '-o'])
                    
                    cmd.extend(['-iname', f'*{query}*', '-print'])
                    
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                    
                    for line in process.stdout:
                        found_path = line.strip()
                        if found_path and found_path not in seen_paths:
                            print(f"  [Found] {found_path}")
                            self.speaker.speak(f"Found related: {os.path.basename(found_path)}.")
                            
                            target_dir = found_path
                            if os.path.isfile(found_path):
                                target_dir = os.path.dirname(found_path)
                                
                            subprocess.Popen(['xdg-open', target_dir], stderr=subprocess.DEVNULL)
                            seen_paths.add(found_path)
                            windows_opened += 1
                            
                            if windows_opened >= max_windows:
                                self.speaker.speak("Limit of opened windows reached.")
                                process.terminate()
                                break
                except Exception as e:
                    print(f"[Error] Search failed in {zone_name}: {e}")
        
        if not seen_paths:
            self.speaker.speak(f"I could not find any files matching {query}.")
            print(f"[Search] Finished. No matches found.")
        else:
             self.speaker.speak("Search complete.")
             print(f"[Search] Completed. Found {len(seen_paths)} items.")

    def _search_and_open(self, command):
        # Format: "search file [name]" or "find [name]"
        keywords = ["search file", "find file", "search for", "find folder", "search folder", "find", "locate"]
        query = self._extract_name(command, keywords)
        query = query.replace("'", "").replace('"', "")
        
        t = threading.Thread(target=self._background_search, args=(query,))
        t.daemon = True
        t.start()
        
        # Immediate response to user
        # self.speaker.speak("Okay, checking system files in the background.")

    def handle_intent(self, tag, command):
        if tag == 'file_create_folder':
            self._create_item(is_folder=True, command=command)
            return True
        elif tag == 'file_create_file':
            self._create_item(is_folder=False, command=command)
            return True
        elif tag == 'file_move':
            self._move_item(command)
            return True
        elif tag == 'file_search':
            self._search_and_open(command)
            return True
        elif tag == 'file_select':
            self._select_item(command)
            return True
        elif tag == 'file_move_here':
            self._move_selected_here(command)
            return True
        return False
