from components.application.close_app import close_application

def kill_process(command, speaker=None, listener=None):
    """Identifies and kills a running process based on user command with confirmation."""
    # Clean the command to get the app name
    ignore_words = ["kill", "close", "terminate", "stop", "running", "program", "application", "process", "task", "the", "please", "cortex"]
    
    words = command.lower().split()
    app_name = " ".join([w for w in words if w not in ignore_words]).strip()
    
    if speaker:
        if not app_name:
            speaker.speak("Which application would you like me to close?")
            return

        speaker.speak(f"Are you sure you want to close {app_name}?")
    
    if listener:
        print("[Debug] Listening for confirmation...")
        confirmation = listener.listen()
        print(f"[Debug] Heard confirmation: '{confirmation}'")
        
        # Loose matching for confirmation
        if not confirmation:
            if speaker:
                speaker.speak("Cancelled.")
            return
            
        conf_lower = confirmation.lower()
        valid_confirms = ["yes", "yeah", "yep", "sure", "do it", "go ahead", "confirm"]
        
        if not any(x in conf_lower for x in valid_confirms):
                if speaker:
                    speaker.speak("Cancelled.")
                return
    
    # Use key-value mapping and robust close logic
    # close_application expects speaker as second arg
    close_application(app_name, speaker)
