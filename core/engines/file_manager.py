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

    def _get_selected_files_from_clipboard(self):
        """
        Detect files currently selected in the active file manager window.
        Uses xdotool to simulate Ctrl+C and xclip to read clipboard.
        Returns list of Path objects for selected files/folders.
        """
        import time
        
        # Check for required dependencies
        try:
            subprocess.run(['which', 'xdotool'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            self.speaker.speak("xdotool is not installed. Please install it to use clipboard-based file selection.")
            print("[FileManager] Error: xdotool not found. Install with: sudo apt install xdotool")
            return []
        
        try:
            subprocess.run(['which', 'xclip'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            self.speaker.speak("xclip is not installed. Please install it to use clipboard-based file selection.")
            print("[FileManager] Error: xclip not found. Install with: sudo apt install xclip")
            return []
        
        try:
            # Simulate Ctrl+C to copy selected files to clipboard
            subprocess.run(['xdotool', 'key', 'ctrl+c'], check=True, stderr=subprocess.DEVNULL)
            
            # Wait briefly for clipboard to update
            time.sleep(0.15)
            
            # Read clipboard content
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-o'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            clipboard_content = result.stdout.strip()
            
            if not clipboard_content:
                return []
            
            # Parse file URIs from clipboard
            # File managers typically copy files as URIs: file:///path/to/file
            selected_paths = []
            
            for line in clipboard_content.split('\n'):
                line = line.strip()
                
                # Handle file:// URI format
                if line.startswith('file://'):
                    # Remove file:// prefix and decode URL encoding
                    from urllib.parse import unquote
                    path_str = unquote(line[7:])  # Remove 'file://'
                    path = Path(path_str)
                    
                    if path.exists():
                        selected_paths.append(path)
                # Handle plain path format (some file managers)
                elif line.startswith('/'):
                    path = Path(line)
                    if path.exists():
                        selected_paths.append(path)
            
            return selected_paths
            
        except subprocess.TimeoutExpired:
            print("[FileManager] Timeout reading clipboard")
            return []
        except Exception as e:
            print(f"[FileManager] Error reading clipboard: {e}")
            return []

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
        """
        Move command handler with clipboard-based file selection.
        - Detects files manually selected in file manager via clipboard
        - Supports voice-based filename for backward compatibility
        - Prompts user to navigate to destination and say 'move here'
        """
        # Extract filename from command (for backward compatibility)
        cleaned_cmd = command.lower().replace("move file", "").replace("move folder", "").replace("move items", "").replace("move selected", "").replace("move", "").strip()
        cleaned_cmd = cleaned_cmd.replace("'", "").replace('"', "")

        # Case 1: "move" or "move selected items" - detect clipboard selection
        if not cleaned_cmd or "selected" in command.lower():
            # Try to get files from clipboard (manually selected in file manager)
            clipboard_files = self._get_selected_files_from_clipboard()
            
            if clipboard_files:
                # Add to selection, avoiding duplicates
                for file_path in clipboard_files:
                    if file_path not in self.selected_items:
                        self.selected_items.append(file_path)
                
                count = len(self.selected_items)
                item_word = "item" if count == 1 else "items"
                self.speaker.speak(f"Selected {count} {item_word}. Navigate to the destination folder and say 'move here' or 'paste here'.")
            elif self.selected_items:
                # Already have selection from previous command
                count = len(self.selected_items)
                item_word = "item" if count == 1 else "items"
                self.speaker.speak(f"You have {count} {item_word} selected. Navigate to the destination folder and say 'move here' or 'paste here'.")
            else:
                # No files selected
                self.speaker.speak("No files are currently selected. Please select files in your file manager and try again.")
            return

        # Case 2: "Move [filename]" - Voice-based selection for backward compatibility
        source_raw = cleaned_cmd
        active_loc = self._get_active_location()
        
        # Try to find the file in current location, desktop, or home
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
            self.speaker.speak(f"Selected {source_raw}. Now navigate to the destination folder and say 'move here' or 'paste here'.")
        else:
            self.speaker.speak(f"I could not find {source_raw} in common locations. Please select the file manually in your file manager and say 'move selected items'.")

    def _select_item(self, command):
        """
        Select a file or folder for later moving.
        Supports clipboard-based selection and voice-based filename selection.
        """
        keywords = ["select file", "select folder", "pick file", "choose file", "select", "pick", "grab", "copy file"]
        name = self._extract_name(command, keywords)
        name = name.replace("'", "").replace('"', "").strip()
        
        # Case 1: "select these" or similar - use clipboard detection
        if not name or name.lower() in ["these", "these files", "selected"]:
            clipboard_files = self._get_selected_files_from_clipboard()
            
            if clipboard_files:
                # Add to selection, avoiding duplicates
                new_count = 0
                for file_path in clipboard_files:
                    if file_path not in self.selected_items:
                        self.selected_items.append(file_path)
                        new_count += 1
                
                total_count = len(self.selected_items)
                if new_count > 0:
                    item_word = "item" if total_count == 1 else "items"
                    self.speaker.speak(f"Selected {new_count} new files. You now have {total_count} {item_word} selected. Navigate to destination and say 'move here'.")
                else:
                    self.speaker.speak(f"These files are already selected. You have {total_count} items selected.")
            else:
                self.speaker.speak("No files are currently selected in your file manager. Please select files and try again.")
            return
        
        # Case 2: Voice-based filename selection (backward compatibility)
        location = self._get_active_location()
        
        # Try to find the file in multiple locations
        possible_locations = [
            (location, location.name),
            (self.desktop_path, "Desktop"),
            (Path.home(), "Home")
        ]
        
        target = None
        found_location = None
        
        for loc, loc_name in possible_locations:
            potential_target = loc / name
            if potential_target.exists():
                target = potential_target
                found_location = loc_name
                break
        
        if not target:
            self.speaker.speak(f"I cannot find {name} in common locations. Please select the file manually in your file manager and say 'select these'.")
            return
        
        # Check if already selected
        if target in self.selected_items:
            self.speaker.speak(f"{name} is already selected.")
            return
            
        self.selected_items.append(target)
        count = len(self.selected_items)
        
        if count == 1:
            location_info = f" from {found_location}" if found_location != location.name else ""
            self.speaker.speak(f"Selected {name}{location_info}. You can select more items or navigate to the destination and say 'move here'.")
        else:
            item_word = "items" if count > 1 else "item"
            self.speaker.speak(f"Selected {name}. You now have {count} {item_word} selected. Navigate to destination and say 'move here'.")

    def _move_selected_here(self, command):
        """
        Move all selected items to the current active location.
        Handles name collisions and provides detailed feedback.
        """
        if not self.selected_items:
            self.speaker.speak("You haven't selected any files to move. Please select files first by saying 'select file' followed by the filename.")
            return

        dest_location = self._get_active_location()
        
        success_count = 0
        skipped_count = 0
        failed_items = []
        
        for item in self.selected_items:
            try:
                # Check if source and destination are the same
                if item.parent == dest_location:
                    skipped_count += 1
                    continue
                
                # Handle name collisions
                destination = dest_location / item.name
                if destination.exists():
                    # Append number to avoid collision
                    base_name = item.stem
                    extension = item.suffix
                    counter = 1
                    while destination.exists():
                        new_name = f"{base_name}_{counter}{extension}"
                        destination = dest_location / new_name
                        counter += 1
                
                shutil.move(str(item), str(destination))
                success_count += 1
            except Exception as e:
                print(f"Error moving {item}: {e}")
                failed_items.append(item.name)
        
        # Clear selection after attempt
        self.selected_items = []
        
        # Provide detailed feedback
        if success_count > 0:
            item_word = "item" if success_count == 1 else "items"
            message = f"Moved {success_count} {item_word} to {dest_location.name}."
            
            if skipped_count > 0:
                message += f" Skipped {skipped_count} already in this location."
            if failed_items:
                message += f" Failed to move: {', '.join(failed_items)}."
                
            self.speaker.speak(message)
        else:
            if skipped_count > 0:
                self.speaker.speak(f"All items are already in {dest_location.name}.")
            else:
                self.speaker.speak("Could not move any items. Please check if the files still exist.")

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
