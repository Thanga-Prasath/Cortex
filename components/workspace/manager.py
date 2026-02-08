import os
import json
import subprocess
import glob
import platform
import shlex
import signal

class WorkspaceManager:
    def __init__(self):
        self.data_dir = os.path.join(os.getcwd(), 'data')
        self.workspace_file = os.path.join(self.data_dir, 'workspaces.json')
        self.workspaces = {}
        self.load_workspaces()
        self.running_processes = []
        self.os_type = platform.system() 

    def load_workspaces(self):
        if not os.path.exists(self.workspace_file):
            return
        try:
            with open(self.workspace_file, 'r') as f:
                self.workspaces = json.load(f)
        except Exception as e:
            print(f"Error loading workspaces: {e}")
            self.workspaces = {}

    def save_workspaces(self):
        try:
            with open(self.workspace_file, 'w') as f:
                json.dump(self.workspaces, f, indent=4)
        except Exception as e:
            print(f"Error saving workspaces: {e}")

    def get_system_apps(self):
        """
        Scans system for applications based on OS.
        Returns a dict: {App Name: Exec Command}
        """
        if self.os_type == "Linux":
            return self._get_linux_apps()
        elif self.os_type == "Windows":
            return self._get_windows_apps()
        elif self.os_type == "Darwin": # macOS
            return self._get_mac_apps()
        else:
            return {}

    def _get_linux_apps(self):
        apps = {}
        paths = [
            '/usr/share/applications',
            '/usr/local/share/applications',
            os.path.expanduser('~/.local/share/applications')
        ]
        for path in paths:
            if not os.path.exists(path):
                continue
            for file_path in glob.glob(os.path.join(path, '*.desktop')):
                try:
                    with open(file_path, 'r', errors='ignore') as f:
                        name, cmd, no_display = None, None, False
                        for line in f:
                            line = line.strip()
                            if line.startswith('Name=') and not name:
                                name = line.split('=', 1)[1]
                            elif line.startswith('Exec=') and not cmd:
                                cmd = line.split('=', 1)[1].split('%')[0].strip()
                            elif line.startswith('NoDisplay=true'):
                                no_display = True
                        if name and cmd and not no_display:
                            apps[name] = cmd
                except:
                    pass
        return dict(sorted(apps.items()))

    def _get_windows_apps(self):
        # Uses PowerShell to find Start Menu shortcuts and UWP apps
        apps = {}
        ps_script = """
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        Get-StartApps | ForEach-Object {
            Write-Output "$($_.Name)|$($_.AppID)"
        }
        """
        try:
            # Run PowerShell command to get apps
            cmd = ["powershell", "-NoProfile", "-Command", ps_script]
            # Use distinct encoding to avoid issues
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            for line in result.stdout.splitlines():
                if '|' in line:
                    try:
                        name, app_id = line.split('|', 1)
                        name = name.strip()
                        app_id = app_id.strip()
                        
                        # Store as shell:AppsFolder command for UWP or regular path if it looks like one (though Get-StartApps returns AppIDs)
                        # Actually Get-StartApps returns AppIDs for everything. 
                        # For desktop apps, AppID is often the path or a specific ID. Launching via shell:AppsFolder works for both if AppID is valid?
                        # Let's test: shell:AppsFolder\Microsoft.WindowsCalculator_8wekyb3d8bbwe!App works.
                        # shell:AppsFolder\Chrome works? No, usually distinct.
                        # But Get-StartApps returns everything needed to launch via shell:AppsFolder usually.
                        
                        apps[name] = f"shell:AppsFolder\\{app_id}"
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Windows app scan failed: {e}")
        return dict(sorted(apps.items()))

    def _get_mac_apps(self):
        apps = {}
        paths = ['/Applications', os.path.expanduser('~/Applications')]
        for path in paths:
            if not os.path.exists(path):
                continue
            for item in os.listdir(path):
                if item.endswith('.app'):
                    name = item[:-4] # Remove .app
                    # Command to open app on mac is 'open -a "App Name"'
                    # But we store the full path for exactness or just name?
                    # 'open -a' works best with names registered, but path is safer.
                    full_path = os.path.join(path, item)
                    apps[name] = f'open -a "{full_path}"' 
        return dict(sorted(apps.items()))

    def create_workspace(self, name, app_list):
        self.load_workspaces() # Sync first just in case
        self.workspaces[name] = app_list
        self.save_workspaces()
        print(f"Workspace '{name}' saved with apps: {app_list}")

    def delete_workspace(self, name):
        self.load_workspaces() # Sync first
        if name in self.workspaces:
            del self.workspaces[name]
            self.save_workspaces()
            return True
        return False

    def launch_workspace(self, name):
        self.load_workspaces() # Sync before launch
        if name not in self.workspaces:
            return False
            
        system_apps = self.get_system_apps()
        apps_to_launch = self.workspaces[name]
        launched_count = 0
        
        for app_entry in apps_to_launch:
            # cmd might be from system_apps (shell:AppsFolder...) or a direct path from old save
            cmd = system_apps.get(app_entry, app_entry)
            
            try:
                print(f"Launching: {cmd}")
                if self.os_type == "Windows":
                    # Handle shell:AppsFolder commands
                    if cmd.lower().startswith("shell:"):
                        # Extract UWP Package Family Name if possible
                        # Format: shell:AppsFolder\PackageFamilyName!AppID
                        uwp_info = None
                        if "!" in cmd and "\\" in cmd:
                            try:
                                # shell:AppsFolder\Microsoft.WindowsCalculator_8wekyb3d8bbwe!App
                                parts = cmd.split("\\")[1].split("!")
                                package_family = parts[0]
                                uwp_info = {'type': 'uwp', 'package': package_family, 'cmd': cmd}
                            except:
                                pass

                        # Use explorer.exe to launch shell commands
                        subprocess.Popen(f'explorer.exe "{cmd}"', shell=True)
                        
                        if uwp_info:
                            self.running_processes.append(uwp_info)
                        # We can't track PID for explorer launches easily, so we only track if we parsed UWP info
                        
                        launched_count += 1
                        continue

                    # On Windows, path with spaces must be quoted for shell=True
                    # Check if cmd is a path that exists
                    if os.path.exists(cmd) or "\\" in cmd:
                        if " " in cmd and not cmd.startswith('"') and not cmd.startswith("'"):
                            cmd = f'"{cmd}"'
                            
                    # Using Popen with shell=True is often required for launching via command string
                    proc = subprocess.Popen(cmd, shell=True)
                else:
                    # Linux/Mac
                    proc = subprocess.Popen(cmd, shell=True, start_new_session=True)
                    
                self.running_processes.append(proc)
                launched_count += 1
            except Exception as e:
                print(f"Failed to launch {app_entry}: {e}")
        
        return launched_count > 0

    def close_current_workspace(self):
        if not self.running_processes:
            return False
            
        print(f"Closing {len(self.running_processes)} applications...")
        
        for item in self.running_processes:
            try:
                # Handle UWP App
                if isinstance(item, dict) and item.get('type') == 'uwp':
                    self._close_uwp_app(item.get('package'))
                    continue

                # Handle Standard Process
                proc = item
                if self.os_type == "Windows":
                    # Windows: terminate() usually works, or taskkill /F /T /PID
                    if proc.poll() is None: # Only if still running
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], 
                                    capture_output=True)
                else:
                    # Linux/macOS: Send SIGTERM to the process group
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception as e:
                print(f"Error terminating process: {e}")
        
        self.running_processes = []
        return True

    def _close_uwp_app(self, package_name):
        """
        Closes a UWP app by searching for its process using the Package Family Name.
        """
        print(f"Attempting to close UWP app: {package_name}")
        try:
            # cmd = 'tasklist /apps /FO CSV'
            # Output format: "Image Name","PID","Mem Usage","Package Name"
            # We look for package_name in the last column
            
            result = subprocess.run(["tasklist", "/apps", "/FO", "CSV"], capture_output=True, text=True)
            if result.returncode != 0:
                print("Failed to run tasklist")
                return

            import csv
            import io
            
            # Parse CSV output
            f = io.StringIO(result.stdout)
            reader = csv.reader(f)
            
            pids_to_kill = []
            
            for row in reader:
                if len(row) >= 4:
                    # row[1] is PID, row[3] is Package Name
                    pid = row[1]
                    pkg = row[3].strip() # Full Package Name
                    
                    # Package Family Name (from shell:AppsFolder) is typically "Name_PublisherId"
                    # Full Package Name (from tasklist) is "Name_Version_Arch_ResourceId_PublisherId"
                    
                    match = False
                    if "_" in package_name:
                        parts = package_name.split("_")
                        name_part = parts[0]
                        pub_id_part = parts[-1]
                        
                        # Robust check: Starts with Name AND Ends with Publisher ID
                        if pkg.lower().startswith(name_part.lower()) and pkg.lower().endswith(pub_id_part.lower()):
                            match = True
                    else:
                        # Fallback for simple names without underscores
                        if package_name.lower() in pkg.lower():
                            match = True
                            
                    if match:
                        pids_to_kill.append(pid)
            
            for pid in pids_to_kill:
                print(f"Killing UWP PID {pid} ({package_name})")
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                
        except Exception as e:
            print(f"Error closing UWP app {package_name}: {e}")

    def get_workspace_names(self):
        self.load_workspaces() # Sync
        return list(self.workspaces.keys())

    def get_workspace_apps(self, name):
        self.load_workspaces() # Sync
        return self.workspaces.get(name, [])
