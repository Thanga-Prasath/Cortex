from components.workspace.manager import WorkspaceManager
# UI components are now imported in the UI process, not here.

class WorkspaceEngine:
    def __init__(self, speaker, status_queue):
        self.speaker = speaker
        self.status_queue = status_queue
        self.manager = WorkspaceManager()
        # Editor/Selector references are no longer held here as they live in another process

    def handle_intent(self, tag, command):
        if tag == "workspace_create":
            self.speaker.speak("Opening workspace creator.")
            self.open_editor()
            return True
            
        elif tag == "workspace_launch":
            name = self._extract_workspace_name(command)
            if name:
                self.speaker.speak(f"Launching workspace {name}.")
                if not self.manager.launch_workspace(name):
                    self.speaker.speak(f"Could not find workspace named {name}.")
            else:
                self.speaker.speak("Which workspace would you like to launch?")
                self.open_selector("LAUNCH")
            return True
            
        elif tag == "workspace_close":
            self.speaker.speak("Closing current workspace applications.")
            if self.manager.close_current_workspace():
                self.speaker.speak("Workspace closed.")
            else:
                self.speaker.speak("No active workspace found to close.")
            return True
            
        elif tag == "workspace_edit":
            self.speaker.speak("Opening workspace editor.")
            self.open_selector("EDIT")
            return True
            
        elif tag == "workspace_remove":
            self.speaker.speak("Which workspace would you like to remove?")
            self.open_selector("REMOVE")
            return True
        
        elif tag == "workspace_list":
            workspaces = self.manager.get_workspace_names()
            if workspaces:
                names = ", ".join(workspaces)
                self.speaker.speak(f"You have the following workspaces: {names}.")
            else:
                self.speaker.speak("You have no saved workspaces.")
            return True

        return False

    def _extract_workspace_name(self, command):
        # command: "open workspace Dev", "launch workspace Gaming"
        triggers = ["open workspace", "launch workspace", "start workspace", "run workspace"]
        for trigger in triggers:
            if command.startswith(trigger):
                name = command[len(trigger):].strip()
                if name:
                    # Match case-insensitively with existing workspaces
                    existing = self.manager.get_workspace_names()
                    for w in existing:
                        if w.lower() == name.lower():
                            return w
                    return name 
        return None

    def open_editor(self, name=None):
        # Send signal to UI process
        # We need access to status_queue. Core engine has it. 
        # But this class is initialized via CoreEngine which has status_queue.
        # We need to pass status_queue to this engine.
        if hasattr(self, 'status_queue') and self.status_queue:
            self.status_queue.put(("WORKSPACE_EDITOR", name))
        else:
            print("Error: status_queue not available in WorkspaceEngine")

    def open_selector(self, mode):
        if hasattr(self, 'status_queue') and self.status_queue:
            self.status_queue.put(("WORKSPACE_SELECTOR", mode))
        else:
            print("Error: status_queue not available in WorkspaceEngine")
