import shutil
from pathlib import Path
from .detection import get_selected_files_from_file_manager

def extract_name(command, keywords):
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

def move_files(command, file_manager_instance):
    """
    Initiates move workflow with multiple detection methods:
    1. If items are already selected (in self.selected_items), acknowledges them
    2. If command suggests GUI selection ("selected", "these", "them"), try GUI detection first
    3. If command contains a specific filename, finds it in active location
    4. Otherwise, attempts to detect selected files from the file manager GUI
    """
    speaker = file_manager_instance.speaker
    
    # Check if items are already selected
    if file_manager_instance.selected_items:
        count = len(file_manager_instance.selected_items)
        item_word = "item" if count == 1 else "items"
        print(f"[FileManager] Using {count} pre-selected {item_word}")
        speaker.speak(f"Ready to move {count} {item_word}. Please navigate to the destination folder and say 'paste here' or 'move here'.")
        return
    
    # Check if command suggests GUI selection
    cmd_lower = command.lower()
    gui_selection_keywords = ["selected", "these", "them", "this", "those"]
    suggests_gui_selection = any(keyword in cmd_lower for keyword in gui_selection_keywords)
    
    if suggests_gui_selection:
        # User is referring to GUI-selected files - try to detect them
        print("[FileManager] Command suggests GUI selection, attempting to detect selected files...")
        selected_files = get_selected_files_from_file_manager()
        
        if selected_files:
            # Successfully detected files
            file_manager_instance.selected_items = selected_files
            count = len(file_manager_instance.selected_items)
            item_word = "item" if count == 1 else "items"
            
            print(f"[FileManager] Successfully detected {count} {item_word}:")
            for item in file_manager_instance.selected_items:
                print(f"  - {item}")
            
            speaker.speak(f"{count} {item_word} selected. Navigate to the destination folder and say 'move here' to complete the move.")
            return
        else:
            # Could not detect GUI selection
            print("[FileManager] No files detected as selected in file manager")
            speaker.speak("I couldn't detect any selected files. Please open your file manager, select the files you want to move, and try again.")
            return
    
    # Try to parse specific filename from command
    # Commands like: "move file test.txt", "move test.txt", "move folder MyFolder"
    keywords = ["move file", "move folder", "move"]
    filename = None
    
    for kw in keywords:
        if cmd_lower.startswith(kw):
            # Extract everything after the keyword
            remainder = command[len(kw):].strip()
            # Exclude GUI selection keywords
            if remainder and remainder.lower() not in gui_selection_keywords:
                filename = remainder
                break
    
    if filename:
        # User specified a filename - find it in the active location
        print(f"[FileManager] Looking for '{filename}' in active location...")
        active_location = file_manager_instance._get_active_location()
        target_path = active_location / filename
        
        if target_path.exists():
            file_manager_instance.selected_items = [target_path]
            print(f"[FileManager] Found exact match: {target_path}")
            speaker.speak(f"Added {filename} to move list. Please navigate to the destination folder and say 'paste here' or 'move here'.")
            return
        
        # Fuzzy / Smart Matching if exact match fails
        # e.g. User says "move space wallpaper", file is "space wallpaper.jpg"
        print(f"[FileManager] Exact match not found. Trying fuzzy/smart matching in {active_location}...")
        
        candidates = []
        try:
            # Scan active location
            for item in active_location.iterdir():
                if item.is_file() or item.is_dir():
                    # Check 1: Stem match (ignoring extension) - HIGH Priority
                    if item.stem.lower() == filename.lower():
                        candidates.append((item, 100)) # Score 100
                    
                    # Check 2: Name contains query - MEDIUM Priority
                    elif filename.lower() in item.name.lower():
                         candidates.append((item, 50))
        except Exception as e:
            print(f"[FileManager] Error scanning active location: {e}")

        if candidates:
            # Sort by score (descending)
            candidates.sort(key=lambda x: x[1], reverse=True)
            best_match = candidates[0][0]
            
            file_manager_instance.selected_items = [best_match]
            print(f"[FileManager] Found smart match: {best_match}")
            speaker.speak(f"Found {best_match.name}. Added to move list. Say 'move here' in destination.")
            return

        else:
            print(f"[FileManager] File not found: {target_path}")
            speaker.speak(f"I could not find {filename} in {active_location.name}.")
            return
    
    # Fallback: Try to detect selected files from file manager GUI
    print("[FileManager] Attempting to detect selected files from file manager...")
    selected_files = get_selected_files_from_file_manager()
    
    if not selected_files:
        print("[FileManager] No files detected as selected")
        speaker.speak("No files are selected. Please select files or folders in your file manager and try again.")
        return
    
    # Store selected items
    file_manager_instance.selected_items = selected_files
    count = len(file_manager_instance.selected_items)
    item_word = "item" if count == 1 else "items"
    
    # Log selected items
    print(f"[FileManager] Successfully detected {count} {item_word}:")
    for item in file_manager_instance.selected_items:
        print(f"  - {item}")
    
    speaker.speak(f"{count} {item_word} selected. Navigate to the destination folder and say 'move here' to complete the move.")

def move_here(command, file_manager_instance):
    """
    Completes the move operation by moving all selected items to current location.
    Handles name collisions and provides detailed feedback.
    """
    speaker = file_manager_instance.speaker
    
    if not file_manager_instance.selected_items:
        speaker.speak("No files are selected to move. Please select files first and say 'move'.")
        return

    dest_location = file_manager_instance._get_active_location()
    
    success_count = 0
    skipped_count = 0
    failed_items = []
    
    for item in file_manager_instance.selected_items:
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
            print(f"[FileManager] Moved: {item} -> {destination}")
        except Exception as e:
            print(f"[FileManager] Error moving {item}: {e}")
            failed_items.append(item.name)
    
    # Clear selection after attempt
    file_manager_instance.selected_items = []
    
    # Provide detailed feedback
    if success_count > 0:
        item_word = "item" if success_count == 1 else "items"
        message = f"Successfully moved {success_count} {item_word} to {dest_location.name}."
        
        if skipped_count > 0:
            message += f" Skipped {skipped_count} already in this location."
        if failed_items:
            message += f" Failed to move: {', '.join(failed_items)}."
            
        speaker.speak(message)
    else:
        if skipped_count > 0:
            speaker.speak(f"All items are already in {dest_location.name}.")
        else:
            speaker.speak("Could not move any items. Please check if the files still exist.")
