import platform
import time
import subprocess
import shutil
import os

# --- Linux X11 Display Fix ---
# pyautogui and pywinctl depend on python-xlib which needs DISPLAY and XAUTHORITY.
# When running from certain terminals or as a service, XAUTHORITY may not be set.
if platform.system() == "Linux":
    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"
    if "XAUTHORITY" not in os.environ:
        xauth_path = os.path.expanduser("~/.Xauthority")
        if os.path.exists(xauth_path):
            os.environ["XAUTHORITY"] = xauth_path

try:
    import pyautogui
except ImportError:
    pyautogui = None
except (SystemExit, Exception) as e:
    print(f"[Automation] pyautogui import failed: {e}")
    pyautogui = None

try:
    import pywinctl
except ImportError:
    pywinctl = None
except Exception as e:
    print(f"[Automation] pywinctl import failed: {e}")
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
        Handles window management.
        - Linux: uses xdotool (works on X11 and Wayland/XWayland)
        - Windows: uses pywinctl (preferred) or pyautogui hotkeys (fallback)
        - macOS: uses pywinctl (preferred) or pyautogui hotkeys (fallback)
        """
        current_os = platform.system()

        try:
            # ---- LINUX: Use xdotool directly (pywinctl/pyautogui don't work on Wayland) ----
            if current_os == "Linux":
                self._handle_window_ops_linux(tag)
                return

            # ---- WINDOWS & macOS: Use pywinctl + pyautogui fallback ----
            if not pyautogui and not pywinctl:
                self.speaker.speak("Window management libraries are not available.")
                return

            active_window = None
            if pywinctl:
                try:
                    active_window = pywinctl.getActiveWindow()
                except Exception:
                    active_window = None

            if tag == 'window_minimize':
                if active_window:
                    active_window.minimize()
                elif pyautogui:
                    if current_os == "Darwin":
                        pyautogui.hotkey('command', 'm')
                    else:
                        pyautogui.hotkey('win', 'down')
                        pyautogui.hotkey('win', 'down')
                self.speaker.speak("Window minimized.")

            elif tag == 'window_maximize':
                if active_window:
                    active_window.maximize()
                elif pyautogui:
                    if current_os == "Darwin":
                        self.speaker.speak("Could not maximize — no active window found.")
                        return
                    else:
                        pyautogui.hotkey('win', 'up')
                self.speaker.speak("Window maximized.")

            elif tag == 'window_restore':
                if active_window:
                    active_window.restore()
                elif pyautogui:
                    if current_os == "Darwin":
                        self.speaker.speak("Could not restore — no active window found.")
                        return
                    else:
                        pyautogui.hotkey('win', 'down')
                self.speaker.speak("Window restored.")

            elif tag == 'window_close':
                if active_window:
                    active_window.close()
                elif pyautogui:
                    if current_os == "Darwin":
                        pyautogui.hotkey('command', 'q')
                    else:
                        pyautogui.hotkey('alt', 'f4')
                self.speaker.speak("Window closed.")

            elif tag == 'window_snap_left':
                if pyautogui:
                    if current_os == "Darwin":
                        self.speaker.speak("Window snapping is not natively supported on macOS.")
                        return
                    else:
                        pyautogui.hotkey('win', 'left')
                self.speaker.speak("Window snapped left.")

            elif tag == 'window_snap_right':
                if pyautogui:
                    if current_os == "Darwin":
                        self.speaker.speak("Window snapping is not natively supported on macOS.")
                        return
                    else:
                        pyautogui.hotkey('win', 'right')
                self.speaker.speak("Window snapped right.")

            elif tag == 'window_switch':
                if pyautogui:
                    if current_os == "Darwin":
                        pyautogui.hotkey('command', 'tab')
                    else:
                        pyautogui.hotkey('alt', 'tab')

            elif tag == 'window_show_desktop':
                if pyautogui:
                    if current_os == "Darwin":
                        pyautogui.hotkey('fn', 'F11')
                    else:
                        pyautogui.hotkey('win', 'd')
                self.speaker.speak("Showing desktop.")

        except Exception as e:
            print(f"Window Op Error: {e}")
            self.speaker.speak("I encountered an issue managing the window.")

    def _handle_window_ops_linux(self, tag):
        """
        Linux-specific window management using evdev UInput (Wayland-compatible).
        Creates a virtual keyboard at kernel level which the compositor accepts as real input.
        Uses GNOME keyboard shortcuts (Super+H=minimize, Alt+F10=maximize, etc).
        """
        try:
            if tag == 'window_minimize':
                # GNOME keybinding: Super+H
                self._linux_send_keys(['KEY_LEFTMETA', 'KEY_H'])
                self.speaker.speak("Window minimized.")

            elif tag == 'window_maximize':
                # GNOME keybinding: Alt+F10 (toggle maximize)
                self._linux_send_keys(['KEY_LEFTALT', 'KEY_F10'])
                self.speaker.speak("Window maximized.")

            elif tag == 'window_restore':
                # GNOME keybinding: Alt+F10 (toggle maximize/restore)
                self._linux_send_keys(['KEY_LEFTALT', 'KEY_F10'])
                self.speaker.speak("Window restored.")

            elif tag == 'window_close':
                # Alt+F4 — universal
                self._linux_send_keys(['KEY_LEFTALT', 'KEY_F4'])
                self.speaker.speak("Window closed.")

            elif tag == 'window_snap_left':
                # GNOME tiling: Super+Left
                self._linux_send_keys(['KEY_LEFTMETA', 'KEY_LEFT'])
                self.speaker.speak("Window snapped left.")

            elif tag == 'window_snap_right':
                # GNOME tiling: Super+Right
                self._linux_send_keys(['KEY_LEFTMETA', 'KEY_RIGHT'])
                self.speaker.speak("Window snapped right.")

            elif tag == 'window_switch':
                # Alt+Tab — universal
                self._linux_send_keys(['KEY_LEFTALT', 'KEY_TAB'])

            elif tag == 'window_show_desktop':
                # GNOME keybinding: Super+D
                self._linux_send_keys(['KEY_LEFTMETA', 'KEY_D'])
                self.speaker.speak("Showing desktop.")

        except Exception as e:
            print(f"[Automation] Linux window op error: {e}")
            self.speaker.speak("I encountered an issue managing the window.")

    def _linux_send_keys(self, key_names):
        """
        Send a keyboard combo on Linux via evdev UInput (kernel-level virtual keyboard).
        This works on both X11 and Wayland because the compositor sees it as real hardware.

        Args:
            key_names: list of evdev key constant names, e.g. ['KEY_LEFTMETA', 'KEY_H']
        """
        try:
            from evdev import UInput, ecodes
        except ImportError:
            # Fallback: try xdotool (X11 only)
            print("[Automation] evdev not available, falling back to xdotool")
            self._linux_send_keys_xdotool(key_names)
            return

        # Resolve key names to evdev key codes
        keycodes = []
        for name in key_names:
            code = getattr(ecodes, name, None)
            if code is None:
                print(f"[Automation] Unknown key: {name}")
                return
            keycodes.append(code)

        # Create virtual keyboard with full key capability set
        capabilities = {ecodes.EV_KEY: list(range(0, 256))}
        ui = UInput(capabilities, name='cortex-virtual-kbd')

        try:
            time.sleep(0.5)  # Wait for compositor to register virtual device

            # Press all keys in order
            for code in keycodes:
                ui.write(ecodes.EV_KEY, code, 1)
                ui.syn()
                time.sleep(0.05)

            time.sleep(0.1)  # Hold combo briefly

            # Release all keys in reverse order
            for code in reversed(keycodes):
                ui.write(ecodes.EV_KEY, code, 0)
                ui.syn()
                time.sleep(0.05)
        finally:
            time.sleep(0.1)
            ui.close()

    def _linux_send_keys_xdotool(self, key_names):
        """Fallback: use xdotool for X11-only systems without evdev."""
        if not shutil.which("xdotool"):
            return
        # Map evdev names to xdotool names
        key_map = {
            'KEY_LEFTMETA': 'super', 'KEY_LEFTALT': 'alt',
            'KEY_H': 'h', 'KEY_D': 'd', 'KEY_TAB': 'Tab',
            'KEY_F4': 'F4', 'KEY_F10': 'F10',
            'KEY_LEFT': 'Left', 'KEY_RIGHT': 'Right',
        }
        xkeys = [key_map.get(k, k.replace('KEY_', '').lower()) for k in key_names]
        subprocess.run(["xdotool", "key", "+".join(xkeys)], timeout=3)

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
                        wf_os = platform.system()
                        try:
                            # 1. Check if it's a directory
                            if os.path.isdir(val):
                                if wf_os == "Windows":
                                    os.startfile(val)
                                elif wf_os == "Darwin":
                                    subprocess.Popen(["open", val])
                                else:  # Linux
                                    subprocess.Popen(["xdg-open", val])
                                self.speaker.speak("Opening folder.")
                            else:
                                # 2. Try executing as a command in a NEW WINDOW
                                if wf_os == "Windows":
                                    cmd_str = f'start cmd /k "{val}"'
                                    subprocess.Popen(cmd_str, shell=True)
                                elif wf_os == "Darwin":
                                    # Open Terminal.app and run the command
                                    apple_script = f'tell application "Terminal" to do script "{val}"'
                                    subprocess.Popen(["osascript", "-e", apple_script])
                                else:  # Linux
                                    terminal = self._find_linux_terminal()
                                    if terminal:
                                        subprocess.Popen([terminal, "-e", "bash", "-c", f'{val}; exec bash'])
                                    else:
                                        # Fallback: run in background
                                        subprocess.Popen(val, shell=True)
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

    def _find_linux_terminal(self):
        """Find an available terminal emulator on Linux."""
        terminals = [
            "x-terminal-emulator",  # Debian/Ubuntu default
            "gnome-terminal",
            "konsole",
            "xfce4-terminal",
            "mate-terminal",
            "tilix",
            "alacritty",
            "kitty",
            "xterm",
        ]
        for term in terminals:
            if shutil.which(term):
                return term
        return None
