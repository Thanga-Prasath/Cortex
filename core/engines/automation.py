import platform
import time
import subprocess
import shutil
try:
    import pyautogui
except (ImportError, Exception):
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

        if tag == 'run_workflow':
            self.execute_workflow()
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
        Quick Note Taking: opens the platform-appropriate text editor.
        Works on Windows, Linux, and macOS.
        """
        self.speaker.speak("What would you like to note down?")
        
        current_os = platform.system()
        
        try:
            if current_os == "Windows":
                # Windows: use notepad.exe (original behavior)
                subprocess.Popen(["notepad.exe"])
                self.speaker.speak("Opening Notepad for your note.")
                
            elif current_os == "Linux":
                # Linux: try common GUI text editors in priority order
                linux_editors = [
                    "gedit",                # GNOME
                    "gnome-text-editor",    # GNOME 42+
                    "kate",                 # KDE
                    "xed",                  # Linux Mint / Cinnamon
                    "mousepad",             # XFCE
                    "pluma",                # MATE
                    "featherpad",           # LXQt
                ]
                
                editor_found = None
                for editor in linux_editors:
                    if shutil.which(editor):
                        editor_found = editor
                        break
                
                if editor_found:
                    subprocess.Popen([editor_found])
                    self.speaker.speak(f"Opening {editor_found} for your note.")
                else:
                    # Fallback: try xdg-open with a temporary text file
                    import tempfile
                    note_file = tempfile.mktemp(suffix=".txt", prefix="sunday_note_")
                    with open(note_file, 'w') as f:
                        f.write("")  # Create empty file
                    
                    if shutil.which("xdg-open"):
                        subprocess.Popen(["xdg-open", note_file])
                        self.speaker.speak("Opening a text editor for your note.")
                    elif shutil.which("nano"):
                        # Last resort: open nano in a terminal
                        terminal = shutil.which("x-terminal-emulator") or \
                                   shutil.which("gnome-terminal") or \
                                   shutil.which("konsole") or \
                                   shutil.which("xterm")
                        if terminal:
                            subprocess.Popen([terminal, "-e", "nano", note_file])
                            self.speaker.speak("Opening nano in a terminal for your note.")
                        else:
                            self.speaker.speak("I couldn't find a text editor on your system.")
                    else:
                        self.speaker.speak("I couldn't find a text editor on your system.")
                        
            elif current_os == "Darwin":
                # macOS: use TextEdit
                subprocess.Popen(["open", "-a", "TextEdit"])
                self.speaker.speak("Opening TextEdit for your note.")
                
            else:
                self.speaker.speak("Note taking is not supported on this operating system.")
                
        except Exception as e:
            print(f"[Note Taking Error] {e}")
            self.speaker.speak("I encountered an error opening the text editor.")

    def execute_workflow(self, workflow_path=None):
        """
        Executes the saved workflow JSON.
        """
        import json, os, time
        
        if not workflow_path:
            workflow_path = os.path.join(os.getcwd(), 'data', 'workflow.json')
            
        if not os.path.exists(workflow_path):
            self.speaker.speak("No workflow found.")
            return

        try:
            with open(workflow_path, 'r') as f:
                data = json.load(f)
                
            nodes = {n['id']: n for n in data['nodes']}
            # Build Adjacency Map: from_id -> list of to_ids
            edges = {} 
            for conn in data['connections']:
                if conn['from'] not in edges:
                    edges[conn['from']] = []
                edges[conn['from']].append(conn['to'])
                
            # Find Start Node
            current_id = None
            for nid, node in nodes.items():
                if node['type'] == 'Start':
                    current_id = nid
                    break
            
            if not current_id:
                print("[Automation] No Start node found.")
                return
                
            print("[Automation] Starting Workflow Execution...")
            self.speaker.speak("Starting automation workflow.")
            
            # BFS Traversal for Branching
            queue = [current_id]
            steps = 0
            MAX_STEPS = 100 # Safety limit for loops
            
            while queue and steps < MAX_STEPS:
                current_id = queue.pop(0)
                steps += 1
                
                node = nodes.get(current_id)
                if not node: continue
                
                node_type = node['type']
                print(f"[Automation] Executing: {node_type}")
                
                # Execute Logic
                node_data = node.get('data', {})
                val = node_data.get('value', '').strip()

                if node_type == 'Speak':
                    text_to_speak = val if val else "No text provided for speak node."
                    self.speaker.speak(text_to_speak)
                    
                elif node_type == 'Delay' or node_type == 'Delay (5s)':
                    # Use provided value if it's a number, else default to 5
                    try:
                        d_time = float(val) if val else 5.0
                    except:
                        d_time = 5.0
                    time.sleep(d_time)
                    
                elif node_type == 'System Command':
                    if val:
                        self.speaker.speak(f"Running command: {val}")
                        try:
                            # 1. Check if it's a directory
                            if os.path.isdir(val):
                                os.startfile(val)
                                self.speaker.speak("Opening folder.")
                            else:
                                # 2. Try executing as a command in a NEW WINDOW
                                # 'start' is a shell command in Windows
                                # 'cmd /k' keeps the window open after execution
                                cmd_str = f'start cmd /k "{val}"'
                                subprocess.Popen(cmd_str, shell=True) 
                        except Exception as e:
                            print(f"[Automation] Command Error: {e}")
                            self.speaker.speak("I could not run that command.")
                    else:
                        self.speaker.speak("No command provided for system node.")
                    
                elif node_type == 'End':
                    print("[Automation] Reached End.")
                    if not queue: # Only say complete if no other branches running
                        self.speaker.speak("Workflow completed.")
                
                # Add children to queue
                children = edges.get(current_id, [])
                for child in children:
                    queue.append(child)
                
                # Small yield for UI responsiveness if needed (though running in thread/process usually)
                time.sleep(0.1) 

                
        except Exception as e:
            print(f"[Automation] Execution Error: {e}")
            self.speaker.speak("Error executing workflow.")
