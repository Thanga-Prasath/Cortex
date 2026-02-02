from .move_files import extract_name

def create_item(is_folder, command, file_manager_instance):
    speaker = file_manager_instance.speaker
    location = file_manager_instance._get_active_location()
    
    keywords = ["named", "called", "folder", "file", "directory"]
    name = extract_name(command, keywords)
    
    # Clean up name (remove quotes if user said "create folder 'foo'")
    name = name.replace("'", "").replace('"', "")
    
    target_path = location / name
    
    try:
        if is_folder:
            target_path.mkdir(parents=True, exist_ok=True)
            speaker.speak(f"Created folder {name} in {location.name}.")
        else:
            target_path.touch(exist_ok=True)
            speaker.speak(f"Created file {name} in {location.name}.")
    except Exception as e:
        speaker.speak(f"I encountered an error creating the item: {str(e)}")
