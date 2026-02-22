import os
import shutil
import subprocess
import pathlib
import json
import threading
from pathlib import Path

# Import components
# Depending on python path, we might need to adjust imports
# Assuming 'components' is at root level and we are running from root
from components.file_manager.active_location import get_active_location
from components.file_manager.detection import get_selected_files_from_file_manager
from components.file_manager.search import background_search
from components.file_manager.move_files import move_files, move_here, extract_name
from components.file_manager.create_item import create_item

class FileManagerEngine:
    def __init__(self, speaker, status_queue=None):
        self.speaker = speaker
        self.status_queue = status_queue
        self.desktop_path = Path.home() / "Desktop"
        self.selected_items = []

    def handle_intent(self, intent, command):
        """
        Routes the intent to the appropriate handler.
        """
        if intent == 'file_create_folder':
            threading.Thread(target=self._create_folder, args=(command,)).start()
            return True
        elif intent == 'file_create_file':
            threading.Thread(target=self._create_file, args=(command,)).start()
            return True
        elif intent == 'file_move':
            threading.Thread(target=self._move_files, args=(command,)).start()
            return True
        elif intent == 'file_move_here':
            threading.Thread(target=self._move_here, args=(command,)).start()
            return True
        elif intent == 'file_search':
            # Extract query
            keywords = ["search", "find", "look for", "searching"]
            query = extract_name(command, keywords)
            
            # Clean query prefixes
            prefixes = ["file ", "folder ", "directory ", "for "]
            for p in prefixes:
                if query.lower().startswith(p):
                    query = query[len(p):].strip()
                    
            if not query:
                return False
                
            threading.Thread(target=self._background_search, args=(query,)).start()
            return True
        elif intent == 'file_search_cancel':
            # Extract query if they said "cancel search for X"
            keywords = ["cancel", "stop", "abort"]
            query = extract_name(command, keywords)
            prefixes = ["search for ", "search ", "the search for "]
            for p in prefixes:
                if query.lower().startswith(p):
                    query = query[len(p):].strip()
            
            import components.file_manager.search as search_mod
            active = list(search_mod.ACTIVE_SEARCHES)
            
            if not active:
                self.speaker.speak("There are no active searches to cancel.")
            elif query and query in active:
                self.cancel_search(query)
            elif len(active) == 1:
                # Only one search running, just cancel it
                self.cancel_search(active[0])
            else:
                # Multiple searches running and no specific name given.
                # Tell UI to open the cancel dialog.
                if self.status_queue:
                    self.speaker.speak("Multiple searches are running. Please select which one to cancel.")
                    self.status_queue.put(("SHOW_CANCEL_DIALOG", active))
            return True
            
        return False

    def _get_active_location(self):
        """
        Delegates to component.
        """
        return get_active_location(self.desktop_path)
    
    def _create_folder(self, command):
        create_item(True, command, self)

    def _create_file(self, command):
        create_item(False, command, self)

    def _move_files(self, command):
        move_files(command, self)

    def _move_here(self, command):
        move_here(command, self)

    def _background_search(self, query):
        if self.status_queue:
            self.status_queue.put(("SEARCHING", (query, True)))
        try:
            background_search(query, self.speaker, self.status_queue)
        finally:
            if self.status_queue:
                self.status_queue.put(("SEARCHING", (query, False)))

    def cancel_search(self, query):
        """Signals the background search worker to abort early."""
        import components.file_manager.search as search_mod
        if query in search_mod.ACTIVE_SEARCHES:
            search_mod.CANCEL_FLAGS[query] = True
            self.speaker.speak(f"Canceling search for {query}.")
