import platform
import time
import subprocess
try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import pywinctl
except ImportError:
    pywinctl = None

try:
    import pyperclip
except ImportError:
    pyperclip = None

class AutomationEngine:
    def __init__(self, speaker):
        self.speaker = speaker

    def handle_intent(self, tag, command=""):
        # --- Phase 1: Dictation (Already Implemented) ---
        if tag == 'dictation_mode':
            return "TOGGLE_DICTATION"

        # --- Phase 2: Window Management ---
        if tag.startswith('window_'):
            self._handle_window_ops(tag)
            return True

        # --- Phase 3: Productivity ---
        if tag.startswith('clipboard_'):
            self._handle_clipboard_ops(tag)
            return True
            
        if tag == 'note_take':
            self._handle_note_taking()
            return True
            
        if tag == 'timer_set':
            self.speaker.speak("Timer functionality is not yet implemented.")
            return True

        return False

    def _handle_window_ops(self, tag):
        """
        Handles window management using pywinctl (preferred) or pyautogui (fallback).
        """
        if not pyautogui and not pywinctl:
            self.speaker.speak("Window management libraries are not available.")
            return
        
        try:
            # Get Active Window
            active_window = None
            if pywinctl:
                active_window = pywinctl.getActiveWindow()
            
            if tag == 'window_minimize':
                if active_window:
                    active_window.minimize()
                else:
                    # Fallback: Win+Down usually minimizes or restores
                    pyautogui.hotkey('win', 'down')
                    pyautogui.hotkey('win', 'down') 
                self.speaker.speak("Window minimized.")

            elif tag == 'window_maximize':
                if active_window:
                    active_window.maximize()
                else:
                    pyautogui.hotkey('win', 'up')
                self.speaker.speak("Window maximized.")

            elif tag == 'window_restore':
                if active_window:
                    active_window.restore()
                else:
                    pyautogui.hotkey('win', 'down')
                self.speaker.speak("Window restored.")

            elif tag == 'window_close':
                if active_window:
                    active_window.close()
                else:
                    pyautogui.hotkey('alt', 'f4')
                self.speaker.speak("Window closed.")

            elif tag == 'window_snap_left':
                # Windows Snap
                pyautogui.hotkey('win', 'left')
                self.speaker.speak("Window snapped left.")
                
            elif tag == 'window_snap_right':
                pyautogui.hotkey('win', 'right')
                self.speaker.speak("Window snapped right.")

            elif tag == 'window_switch':
                pyautogui.hotkey('alt', 'tab')
                # No speech for this - user is switching windows
                
            elif tag == 'window_show_desktop':
                pyautogui.hotkey('win', 'd')
                self.speaker.speak("Showing desktop.")

        except Exception as e:
            print(f"Window Op Error: {e}")
            self.speaker.speak("I encountered an issue managing the window.")

    def _handle_clipboard_ops(self, tag):
        """
        Handles clipboard operations using pyperclip.
        """
        if not pyperclip:
            self.speaker.speak("Clipboard module missing.")
            return

        if tag == 'clipboard_view':
            content = pyperclip.paste()
            if content:
                # Limit speech length
                preview = content[:100] + "..." if len(content) > 100 else content
                self.speaker.speak(f"Clipboard contains: {preview}")
            else:
                self.speaker.speak("Clipboard is empty.")

        elif tag == 'clipboard_clear':
            pyperclip.copy("")
            self.speaker.speak("Clipboard cleared.")

    def _handle_note_taking(self):
        """
        Quick Note Taking: appends to a local notes.txt file.
        """
        self.speaker.speak("What would you like to note down?")
        # Note: This requires a callback or blocking listen, which we don't have direct access 
        # to inside this class easily without passing 'listener'. 
        # IMPORTANT: Engines usually receive (tag, command). 
        # If the command was "note down buy milk", we can extract "buy milk".
        # If just "take a note", we might need to ask. 
        # FOR NOW: Let's assume we capture from the initial command if possible, 
        # or simplified flow where we just open Notepad.
        
        # Simple implementation: Open Notepad
        subprocess.Popen(["notepad.exe"])
        self.speaker.speak("Opening Notepad for your note.")
