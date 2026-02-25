import os
import platform
import subprocess
import json
import shutil

class AppMapper:
    def __init__(self):
        self.os_type = platform.system()
        self.apps = {}
        self._load_apps()

    def _load_apps(self):
        """Loads installed applications into a dictionary {name: command}."""
        if self.os_type == 'Windows':
            self._load_windows_apps()
        elif self.os_type == 'Linux':
            self._load_linux_apps()
        elif self.os_type == 'Darwin':
            self._load_macos_apps()

    def _load_windows_apps(self):
        """
        Uses PowerShell Get-StartApps to find UWP and Win32 apps.
        Using a temp file to avoid pipe encoding/buffering issues.
        """
        temp_file = os.path.join(os.getenv('TEMP'), 'apps.json')
        try:
            # Output to a file with Ascii encoding or set encoding in PS
            cmd = f"powershell -Command \"Get-StartApps | Select-Object Name, AppID | ConvertTo-Json | Out-File -FilePath '{temp_file}' -Encoding UTF8\""
            subprocess.run(cmd, shell=True, check=True)
            
            if not os.path.exists(temp_file):
                print("[AppMapper] output file not found.")
                return

            with open(temp_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                
            if not content.strip():
                 return
            
            try:
                apps_list = json.loads(content)
            except json.JSONDecodeError:
                # Sometimes PS output has issues, try cleaning
                print(f"[AppMapper] JSON Decode Error in file.")
                return

            # If only one app, powershell returns a dict, not a list
            if isinstance(apps_list, dict):
                apps_list = [apps_list]
                
            for item in apps_list:
                name = item.get('Name', '').lower()
                app_id = item.get('AppID', '')
                if name and app_id:
                    # Smart Filtering: Ignore junk
                    # 1. Ignore text/help files by extension in AppID (common for Start Menu shortcuts)
                    lower_id = app_id.lower()
                    if lower_id.endswith('.txt') or lower_id.endswith('.url') or lower_id.endswith('.html') or lower_id.endswith('.xml'):
                        continue
                        
                    # 2. Ignore common noise words in Name
                    noise_words = ["uninstall", "readme", "help", "license", "setup", "install"]
                    if any(w in name for w in noise_words):
                        continue
                        
                    # 3. Ignore very short noise words if they map to deep paths
                    # "what" -> ...\WhatsNew.txt was the issue. 
                    # If name is short (< 4 chars) and not in a whitelist, and AppID looks like a file path...
                    # Whitelist: cmd, vlc, git
                    whitelist_short = ["cmd", "vlc", "git", "arc", "vim", "npm"]
                    if len(name) < 4 and name not in whitelist_short:
                         # If it points to a file that isn't an exe/lnk, skip
                         if "." in lower_id and not lower_id.endswith(".exe") and not lower_id.endswith(".lnk"):
                              continue

                    self.apps[name] = f"shell:AppsFolder\\{app_id}"
                    
                    # Also strip typical suffixes and handle "WhatsApp" specifically if needed
                    clean_name = name.replace(" app", "").replace(" for windows", "").strip()
                    if clean_name != name and len(clean_name) > 2:
                        self.apps[clean_name] = f"shell:AppsFolder\\{app_id}"
                        
        except Exception as e:
            print(f"[AppMapper] Error loading Windows apps: {e}")
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def _load_linux_apps(self):
        """
        Scans .desktop files in standard locations.
        """
        paths = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications")
        ]
        
        for path in paths:
            if not os.path.exists(path):
                continue
                
            for file in os.listdir(path):
                if file.endswith(".desktop"):
                    try:
                        self._parse_desktop_file(os.path.join(path, file))
                    except:
                        pass

    def _parse_desktop_file(self, path):
        name = None
        exec_cmd = None
        with open(path, 'r', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith("Name=") and not name:
                    name = line.split("=", 1)[1].lower()
                elif line.startswith("Exec=") and not exec_cmd:
                    exec_cmd = line.split("=", 1)[1]
                    # Remove %u, %F etc placeholders
                    exec_cmd = exec_cmd.split("%")[0].strip()
                    
        if name and exec_cmd:
            self.apps[name] = exec_cmd

    def _load_macos_apps(self):
        # Placeholder for macOS
        pass

    def get_app_command(self, app_name):
        """Returns the command to launch the app, or None."""
        return self.apps.get(app_name.lower())

    def search_app(self, query):
        """Fuzzy search for an app."""
        query = query.lower().strip()

        # Direct match
        if query in self.apps:
            return self.apps[query]

        # Safety guard: do NOT substring-search on very short queries —
        # "to" is inside "navigator", "on" is inside "anaconda", etc.
        if len(query) < 4:
            return None

        # Word-boundary substring match:
        # The query must start at a word boundary inside the app name,
        # NOT match mid-word (e.g. "window" must match "windows" at pos 0,
        # not match "camerawindow" mid-string).
        import re
        pattern = re.compile(r'\b' + re.escape(query), re.IGNORECASE)
        for name, cmd in self.apps.items():
            if pattern.search(name):
                return cmd

        return None
