import json
import os
import platform
import difflib
import subprocess
from core.runtime_path import get_app_root

class StaticCommandEngine:
    def __init__(self, speaker, listener=None):
        self.speaker = speaker
        self.listener = listener
        self.os_type = platform.system().lower()
        self.commands = self._load_commands()
        
    def _load_commands(self):
        """Loads the JSON database."""
        json_path = os.path.join(get_app_root(), 'data', 'terminal_commands.json')
        if not os.path.exists(json_path):
            print(f"[Static] Error: Database not found at {json_path}")
            return {}
            
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                print(f"[Static] Loaded command database with {sum(len(v) for v in data.values())} entries.")
                return data
        except Exception as e:
            print(f"[Static] Error loading database: {e}")
            return {}

    def _find_best_match(self, user_text):
        """
        Uses fuzzy matching to find the best command.
        Returns (command_key, category, confidence)
        """
        # Flatten the database for searching
        search_space = [] 
        
        for category, items in self.commands.items():
            for key, details in items.items():
                for pattern in details['patterns']:
                    search_space.append((pattern, key, category))
        
        # Extract just the text patterns for matching
        patterns = [p[0] for p in search_space]
        
        # Find closest match
        matches = difflib.get_close_matches(user_text, patterns, n=1, cutoff=0.5)
        
        if matches:
            best_pattern = matches[0]
            # Find the original entry
            for p, k, c in search_space:
                if p == best_pattern:
                    return k, c, difflib.SequenceMatcher(None, user_text, best_pattern).ratio()
                    
        # Check for direct keyword containment
        for p, k, c in search_space:
            if p in user_text:
                 return k, c, 0.9 # High confidence
                 
        return None, None, 0.0

    def _get_confirmation(self, action_name="perform this action"):
        """Asks the user for confirmation and returns True/False."""
        self.speaker.speak(f"Are you sure you want to {action_name}?")
        print(f"[Static] Waiting for confirmation for '{action_name}' (y/n)...")
        
        if self.listener:
            # Short timeout for confirmation
            response = self.listener.listen(timeout=5)
            if response:
                response = response.lower()
                affirmatives = ["yes", "yeah", "yup", "sure", "confirmed", "do it"]
                if any(word in response for word in affirmatives):
                    return True
        else:
             # Fallback for testing/cli
             pass
             
        return False

    def _run_in_terminal(self, command, title, os_type):
        """Executes the command in a new terminal window."""
        try:
            if os_type == 'windows':
                subprocess.Popen(f'start "{title}" cmd /k "{command}"', shell=True)
            elif os_type == 'linux':
                terminals = ['gnome-terminal', 'konsole', 'xterm']
                for term in terminals:
                    try:
                        if term == 'gnome-terminal':
                            subprocess.Popen([term, '--', 'bash', '-c', f'{command}; exec bash'])
                        elif term == 'konsole':
                             subprocess.Popen([term, '-e', 'bash', '-c', f'{command}; exec bash'])
                        else:
                            subprocess.Popen([term, '-e', f'{command}; bash'])
                        break
                    except FileNotFoundError:
                        continue
            elif os_type == 'macos':
                subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "{command}"'])
        except Exception as e:
            print(f"[Static] Execution Error: {e}")
            self.speaker.speak("I encountered an error executing that command.")

    def handle_intent(self, tag, user_input):
        """
        Handles the intent by looking up the command.
        """
        # Mode 1: Intent-Based Execution (High Precision)
        if tag:
            # Check if the tag corresponds exactly to a command key
            for category, items in self.commands.items():
                if tag in items:
                    # Found exact match for tag
                    return self._execute_command(tag, category, items[tag])
            
            # If tag is provided but not found, we should NOT fall back to fuzzy matching
            # logic, because another engine (like GeneralEngine) is likely the intended target.
            return False

        # Mode 2: Fallback / Text-Based Matching (Fuzzy)
        if not self.commands:
            return False

        key, category, confidence = self._find_best_match(user_input.lower())
        
        if key and confidence > 0.6: # Increased threshold for safety
            return self._execute_command(key, category, self.commands[category][key], confidence)
        
        return False

    def _execute_command(self, key, category, command_entry, confidence=1.0):
        """Helper to execute."""
        # Safety Check
        if command_entry.get('confirm', False):
             action = key.replace('_', ' ')
             if not self._get_confirmation(action):
                 self.speaker.speak(f"{action.title()} cancelled.")
                 return True
        
        # Get the command
        cmd_info = command_entry['cmd']
        sys_os = self.os_type
        if sys_os == 'darwin': sys_os = 'macos'
        
        cmd = cmd_info.get(sys_os)
        if not cmd:
            cmd = cmd_info.get('linux') # Fallback
            
        if cmd:
            if confidence < 1.0:
                 print(f"[Static] Match: {key} ({confidence:.2f}) -> {cmd}")
            else:
                 print(f"[Static] Executing: {key}")
                 
            self.speaker.speak(f"Executing {key.replace('_', ' ')}.")
            self._run_in_terminal(cmd, f"Task: {key.replace('_', ' ').title()}", self.os_type)
            return True
        return False
