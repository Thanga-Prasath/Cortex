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
    def __init__(self, speaker, status_queue=None):
        self.speaker = speaker
        self.status_queue = status_queue

    def handle_intent(self, tag, command=""):
        # --- Phase 1: Dictation (Already Implemented) ---
        if tag == 'dictation_mode':
            return "TOGGLE_DICTATION"

        # --- Phase 2: Window Management ---
        if tag.startswith('window_'):
            self._handle_window_ops(tag, command)
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
            
        if tag == 'list_automations':
            if self.status_queue:
                self.speaker.speak("Here are your automations.")
                self.status_queue.put(("AUTOMATION_LIST", None))
            else:
                self.speaker.speak("UI is not connected, cannot show automations.")
            return True

        if tag == 'run_automation_by_number':
            self.handle_run_by_numbers(command)
            return True

        if tag == 'run_automation_by_name':
            self.handle_run_by_name(command)
            return True

        return False

    def _get_sorted_automation_names(self):
        """Returns automations sorted with primary first, then alphabetically."""
        import json, glob, os
        data_dir = os.path.join(os.getcwd(), 'data', 'automations')

        primary = None
        state_file = os.path.join(data_dir, 'state.json')
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    primary = json.load(f).get('primary', None)
            except: pass

        json_files = glob.glob(os.path.join(data_dir, "*.json"))
        names = []
        for f in json_files:
            name = os.path.basename(f).replace(".json", "")
            if name != "state":
                names.append(name)

        names.sort()
        if primary and primary in names:
            names.remove(primary)
            names.insert(0, primary)

        return names

    def handle_run_by_numbers(self, command):
        """Extract numbers from command and run corresponding automations by index."""
        import re
        numbers = re.findall(r'\d+', command)
        if not numbers:
            self.speaker.speak("Please specify which automation number to run.")
            return

        names = self._get_sorted_automation_names()
        if not names:
            self.speaker.speak("No automations found.")
            return

        ran = []
        for n_str in numbers:
            idx = int(n_str) - 1  # 1-based to 0-based
            if 0 <= idx < len(names):
                name = names[idx]
                ran.append(name)
                self.execute_workflow(workflow_name=name)
            else:
                self.speaker.speak(f"Automation number {n_str} does not exist.")

        if ran:
            label = " and ".join(ran)
            print(f"[Automation] Ran by number: {label}")

    def handle_run_by_name(self, command):
        """Extract automation name from command and run it by fuzzy name match."""
        import re
        cmd = command.lower()
        # Strip trigger phrases to get the name token(s)
        # Supports: "run {name} automation", "run automation {name}", "start {name}"
        for pat in [
            r'run\s+(.+?)\s+automation\b',
            r'(?:run|start|execute)\s+automation\s+(.+)',
            r'(?:run|start|execute)\s+(.+)',
        ]:
            m = re.search(pat, cmd)
            if m:
                name_query = m.group(1).strip()
                break
        else:
            self.speaker.speak("Which automation would you like me to run?")
            return

        names = self._get_sorted_automation_names()
        if not names:
            self.speaker.speak("No automations found.")
            return

        # Fuzzy match: find best matching automation name
        from difflib import get_close_matches
        matches = get_close_matches(name_query, [n.lower() for n in names], n=1, cutoff=0.4)
        if matches:
            matched_lower = matches[0]
            # Resolve back to original cased name
            matched_name = next(n for n in names if n.lower() == matched_lower)
            print(f"[Automation] Running by name: '{name_query}' → '{matched_name}'")
            self.execute_workflow(workflow_name=matched_name)
        else:
            self.speaker.speak(f"I couldn't find an automation named {name_query}.")

    def _handle_window_ops(self, tag, command=""):
        """
        Handles window management.
        - Linux: uses evdev UInput (Wayland) or xdotool (X11)
        - Windows: uses pywinctl (preferred) or pyautogui hotkeys (fallback)
        - macOS: uses pywinctl (preferred) or pyautogui hotkeys (fallback)
        """
        current_os = platform.system()

        try:
            # ---- LINUX: Use evdev UInput / xdotool ----
            if current_os == "Linux":
                self._handle_window_ops_linux(tag, command)
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

            elif tag == 'window_switch_to':
                self._switch_to_app(command, current_os)

            elif tag == 'window_show_all':
                self._tile_all_windows(current_os)

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

    def _handle_window_ops_linux(self, tag, command=""):
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

            elif tag == 'window_switch_to':
                self._switch_to_app(command, "Linux")

            elif tag == 'window_show_all':
                self._tile_all_windows("Linux")

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

    # =============================================
    #  Switch To Specific App Window
    # =============================================
    def _extract_app_name(self, command):
        """
        Extract the application name from a voice command.
        e.g. "switch to Firefox" → "firefox"
             "go to chrome" → "chrome"
             "focus on terminal" → "terminal"
        """
        command_lower = command.lower().strip()
        # Remove common prefixes
        prefixes = [
            "switch to ", "go to ", "focus on ", "bring up ",
            "show me ", "activate ", "open ", "focus "
        ]
        for prefix in prefixes:
            if command_lower.startswith(prefix):
                app_name = command_lower[len(prefix):].strip()
                # Remove trailing "window" or "app"
                for suffix in [" window", " app", " application"]:
                    if app_name.endswith(suffix):
                        app_name = app_name[:-len(suffix)].strip()
                return app_name
        # Fallback: return last word(s) after removing common words
        words = command_lower.split()
        stop_words = {'the', 'a', 'an', 'to', 'on', 'my', 'please', 'window', 'app'}
        meaningful = [w for w in words if w not in stop_words]
        return meaningful[-1] if meaningful else ""

    def _is_app_running(self, app_name, current_os):
        """
        Check if an application is currently running.
        Returns True/False.
        """
        if current_os == "Windows":
            # Use pywinctl to check if any window title contains the app name (case-insensitive)
            if pywinctl:
                try:
                    all_windows = pywinctl.getAllWindows()
                    app_lower = app_name.lower()
                    for w in all_windows:
                        title = (w.title if hasattr(w, 'title') else '').lower()
                        if app_lower in title:
                            return True
                except Exception:
                    pass
            # Fallback: tasklist — map common aliases to actual process names
            process_aliases = {
                "edge": "msedge", "microsoft edge": "msedge",
                "chrome": "chrome", "google chrome": "chrome",
                "firefox": "firefox", "code": "Code", "vscode": "Code",
                "explorer": "explorer", "file explorer": "explorer",
                "notepad": "notepad", "whatsapp": "WhatsApp",
                "spotify": "Spotify", "word": "WINWORD",
                "excel": "EXCEL", "powerpoint": "POWERPNT",
                "terminal": "WindowsTerminal", "cmd": "cmd",
            }
            search_name = process_aliases.get(app_name.lower(), app_name)
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {search_name}*"],
                    capture_output=True, text=True, timeout=5
                )
                return search_name.lower() in result.stdout.lower()
            except Exception:
                return False
        else:
            # Linux & macOS: use pgrep
            try:
                result = subprocess.run(
                    ["pgrep", "-fi", app_name],
                    capture_output=True, text=True, timeout=5
                )
                return result.returncode == 0
            except Exception:
                return False

    def _switch_to_app(self, command, current_os):
        """
        Switch to a specific application window.
        Extracts app name from command, checks if running, then activates.
        """
        app_name = self._extract_app_name(command)
        if not app_name:
            self.speaker.speak("Which application would you like me to switch to?")
            return

        print(f"[Automation] Switching to app: '{app_name}'")

        # Check if the app is running
        if not self._is_app_running(app_name, current_os):
            self.speaker.speak(f"{app_name} is not currently running.")
            return

        try:
            if current_os == "Linux":
                self._switch_to_app_linux(app_name)
            elif current_os == "Darwin":
                self._switch_to_app_macos(app_name)
            else:  # Windows
                self._switch_to_app_windows(app_name)
        except Exception as e:
            print(f"[Automation] Switch to app error: {e}")
            self.speaker.speak(f"Could not switch to {app_name}.")

    def _switch_to_app_linux(self, app_name):
        """Activate an app window on Linux using wmctrl or xdotool."""
        # Try wmctrl first (works for X11 / XWayland apps)
        if shutil.which("wmctrl"):
            result = subprocess.run(
                ["wmctrl", "-a", app_name],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.speaker.speak(f"Switched to {app_name}.")
                return

        # Try xdotool search + activate
        if shutil.which("xdotool"):
            result = subprocess.run(
                ["xdotool", "search", "--name", app_name],
                capture_output=True, text=True, timeout=5
            )
            window_ids = result.stdout.strip().split('\n')
            if window_ids and window_ids[0]:
                subprocess.run(
                    ["xdotool", "windowactivate", window_ids[0]],
                    timeout=5
                )
                self.speaker.speak(f"Switched to {app_name}.")
                return

        # Fallback: try gtk-launch with .desktop file
        try:
            subprocess.run(
                ["gtk-launch", f"{app_name.lower()}"],
                capture_output=True, timeout=5
            )
            self.speaker.speak(f"Switched to {app_name}.")
        except Exception:
            self.speaker.speak(f"Could not switch to {app_name}. Try using Alt+Tab.")

    def _switch_to_app_windows(self, app_name):
        """Activate an app window on Windows using pywinctl."""
        if not pywinctl:
            self.speaker.speak("Window control library is not available.")
            return
        try:
            # Case-insensitive window title search
            all_windows = pywinctl.getAllWindows()
            app_lower = app_name.lower()
            matched = [w for w in all_windows
                       if app_lower in (w.title if hasattr(w, 'title') else '').lower()
                       and (w.title or '').strip()]
            if matched:
                win = matched[0]
                if hasattr(win, 'activate'):
                    win.activate()
                self.speaker.speak(f"Switched to {app_name}.")
            else:
                self.speaker.speak(f"Could not find {app_name} window.")
        except Exception as e:
            print(f"[Automation] Windows switch error: {e}")
            self.speaker.speak(f"Could not switch to {app_name}.")

    def _switch_to_app_macos(self, app_name):
        """Activate an app window on macOS using osascript."""
        try:
            subprocess.run(
                ["osascript", "-e",
                 f'tell application "{app_name}" to activate'],
                capture_output=True, timeout=5
            )
            self.speaker.speak(f"Switched to {app_name}.")
        except Exception as e:
            print(f"[Automation] macOS switch error: {e}")
            self.speaker.speak(f"Could not switch to {app_name}.")

    # =============================================
    #  Tile All Windows (Hyprland-style)
    # =============================================
    def _tile_all_windows(self, current_os):
        """
        Tile all visible windows in an equal grid layout.
        Linux: Activities Overview (Super key) on Wayland, wmctrl on X11.
        Windows/macOS: pywinctl move+resize.
        """
        try:
            if current_os == "Linux":
                self._tile_all_linux()
            elif current_os == "Darwin":
                self._tile_all_macos()
            else:  # Windows
                self._tile_all_pywinctl()
        except Exception as e:
            print(f"[Automation] Tile all error: {e}")
            self.speaker.speak("I encountered an issue arranging the windows.")

    def _tile_all_linux(self):
        """Tile windows on Linux."""
        import math

        # Try wmctrl tiling first (works on X11 / XWayland)
        if shutil.which("wmctrl"):
            try:
                # Get window list
                result = subprocess.run(
                    ["wmctrl", "-lG"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    lines = [l for l in result.stdout.strip().split('\n')
                             if not l.strip().startswith('-1')]  # skip desktop
                    if lines:
                        # Get screen size from first desktop line or default
                        try:
                            desk_result = subprocess.run(
                                ["wmctrl", "-d"],
                                capture_output=True, text=True, timeout=3
                            )
                            # Parse "DG: WIDTHxHEIGHT" from output
                            for part in desk_result.stdout.split():
                                if 'x' in part and part.replace('x', '').isdigit():
                                    w, h = part.split('x')
                                    screen_w, screen_h = int(w), int(h)
                                    break
                            else:
                                screen_w, screen_h = 1920, 1080
                        except Exception:
                            screen_w, screen_h = 1920, 1080

                        n = len(lines)
                        cols = math.ceil(math.sqrt(n))
                        rows = math.ceil(n / cols)
                        cell_w = screen_w // cols
                        cell_h = screen_h // rows

                        for i, line in enumerate(lines):
                            win_id = line.split()[0]
                            col = i % cols
                            row = i // cols
                            x = col * cell_w
                            y = row * cell_h
                            # wmctrl: -e gravity,x,y,width,height
                            subprocess.run(
                                ["wmctrl", "-ir", win_id, "-e",
                                 f"0,{x},{y},{cell_w},{cell_h}"],
                                timeout=3
                            )

                        self.speaker.speak(f"Arranged {n} windows in a grid.")
                        return
            except Exception as e:
                print(f"[Automation] wmctrl tiling failed: {e}")

        # Fallback: GNOME Activities Overview (Super key press)
        self._linux_send_keys(['KEY_LEFTMETA'])
        self.speaker.speak("Showing all windows in overview.")

    def _tile_all_pywinctl(self):
        """Tile windows using pywinctl (Windows/macOS)."""
        import math

        if not pywinctl:
            self.speaker.speak("Window control library is not available.")
            return

        try:
            all_windows = pywinctl.getAllWindows()
        except Exception:
            self.speaker.speak("Could not get window list.")
            return

        # Filter: visible, non-minimized, has a title
        visible = []
        for w in all_windows:
            try:
                title = w.title if hasattr(w, 'title') else str(w)
                if not title or title.strip() == '':
                    continue
                # Skip system windows and the Cortex UI
                skip_titles = ['', 'Program Manager', 'Desktop', 'Cortex']
                if title in skip_titles:
                    continue
                visible.append(w)
            except Exception:
                continue

        if not visible:
            self.speaker.speak("No windows to arrange.")
            return

        # Get screen size
        try:
            if pyautogui:
                screen_w, screen_h = pyautogui.size()
            else:
                screen_w, screen_h = 1920, 1080
        except Exception:
            screen_w, screen_h = 1920, 1080

        n = len(visible)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        cell_w = screen_w // cols
        cell_h = screen_h // rows

        for i, win in enumerate(visible):
            col = i % cols
            row = i // cols
            x = col * cell_w
            y = row * cell_h
            try:
                win.moveTo(x, y)
                win.resizeTo(cell_w, cell_h)
            except Exception as e:
                print(f"[Automation] Could not tile window '{win.title}': {e}")

        self.speaker.speak(f"Arranged {n} windows in a grid.")

    def _tile_all_macos(self):
        """Tile windows on macOS."""
        # Try pywinctl tiling first
        if pywinctl:
            self._tile_all_pywinctl()
            return
        # Fallback: Mission Control (Ctrl+Up or F3)
        if pyautogui:
            pyautogui.hotkey('ctrl', 'up')
            self.speaker.speak("Showing Mission Control.")
        else:
            self.speaker.speak("Window tiling is not available.")

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

    def execute_workflow(self, workflow_name=None):
        """
        Executes the saved workflow JSON.
        """
        import json, os, time
        
        data_dir = os.path.join(os.getcwd(), 'data', 'automations')
        
        # Determine which workflow to run
        if not workflow_name:
            state_file = os.path.join(data_dir, 'state.json')
            if os.path.exists(state_file):
                try:
                    with open(state_file, 'r') as f:
                        state = json.load(f)
                        workflow_name = state.get('primary', 'Default')
                except:
                    workflow_name = 'Default'
            else:
                workflow_name = 'Default'
                
        # Handle legacy or new path
        workflow_path = os.path.join(data_dir, f'{workflow_name}.json')
        
        # Backwards compatibility check
        legacy_path = os.path.join(os.getcwd(), 'data', 'workflow.json')
        if not os.path.exists(workflow_path) and os.path.exists(legacy_path):
            workflow_path = legacy_path
            
        if not os.path.exists(workflow_path):
            self.speaker.speak(f"No automation found named {workflow_name}.")
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
