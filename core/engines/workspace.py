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
                self.manager.launch_workspace(name)
                return True
            elif name is False:
                # Name was spoken but no workspace matched — re-prompt with list
                existing = self.manager.get_workspace_names()
                if existing:
                    names_str = ", ".join(existing)
                    self.speaker.speak(f"I couldn't find that workspace. You have: {names_str}. Which one should I launch?")
                else:
                    self.speaker.speak("You have no saved workspaces.")
                    return True
                self.open_selector("LAUNCH")
                return "PENDING"
            else:
                # No name given at all — prompt and show GUI
                self.speaker.speak("Which workspace should I launch? You can also select one from the list.")
                self.open_selector("LAUNCH")
                return "PENDING"
            
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
            name = self._extract_workspace_name(command)
            if name:
                if self.manager.delete_workspace(name):
                    self.speaker.speak(f"Workspace {name} removed.")
                else:
                    self.speaker.speak(f"Could not remove workspace {name}.")
                return True
            elif name is False:
                # Name spoken but not matched — re-prompt with list
                existing = self.manager.get_workspace_names()
                if existing:
                    names_str = ", ".join(existing)
                    self.speaker.speak(f"I couldn't find that workspace. You have: {names_str}. Which one should I remove?")
                else:
                    self.speaker.speak("You have no saved workspaces.")
                    return True
                self.open_selector("REMOVE")
                return "PENDING"
            else:
                # No name given — hybrid prompt
                self.speaker.speak("Which workspace should I remove? You can also select one from the list.")
                self.open_selector("REMOVE")
                return "PENDING"
        
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
        """
        Extract and fuzzy-match a workspace name from a command string.
        
        Returns:
            str   — the canonical workspace name (matched)
            False — a name was provided but no workspace matched
            None  — no name was present at all (e.g. bare "launch workspace")
        """
        cmd = command.strip().lower()
        
        # Strip trigger phrases to isolate the candidate name
        triggers = [
            "open workspace", "launch workspace", "start workspace",
            "run workspace", "load workspace", "switch workspace"
        ]
        candidate = None
        for trigger in triggers:
            if cmd.startswith(trigger):
                after = cmd[len(trigger):].strip()
                if after:
                    candidate = after
                else:
                    return None  # Bare trigger with nothing after it
                break
        
        # If no trigger found, treat the entire command as the candidate name
        # (This is the PENDING-fill path: command = "browsers", "point", etc.)
        if candidate is None:
            if cmd:
                candidate = cmd
            else:
                return None
        
        # Fuzzy match against all saved workspaces (case-insensitive)
        existing = self.manager.get_workspace_names()
        
        # Pass 1: exact match (case-insensitive)
        for w in existing:
            if w.lower() == candidate:
                return w
        
        # Pass 2: workspace name is contained in candidate (e.g. "browsers workspace")
        for w in existing:
            if w.lower() in candidate:
                return w
        
        # Pass 3: candidate is contained in workspace name (e.g. "browser" → "Browsers")
        for w in existing:
            if candidate in w.lower():
                return w
        
        # Pass 4: any word in the candidate matches any word in a workspace name
        candidate_words = set(candidate.split())
        for w in existing:
            ws_words = set(w.lower().split())
            if candidate_words & ws_words:  # non-empty intersection
                return w
        
        # A name was spoken but nothing matched
        return False

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
