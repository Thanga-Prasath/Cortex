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
        # Uses PowerShell to find Start Menu shortcuts
        apps = {}
        ps_script = """
        $paths = @(
            [Environment]::GetFolderPath('CommonStartMenu'),
            [Environment]::GetFolderPath('StartMenu')
        )
        $shortcuts = Get-ChildItem -Path $paths -Recurse -Include *.lnk
        foreach ($s in $shortcuts) {
            $sh = New-Object -ComObject WScript.Shell
            $target = $sh.CreateShortcut($s.FullName).TargetPath
            if ($target -match '\\.exe$') {
                Write-Output "$($s.BaseName)|$target"
            }
        }
        """
        try:
            # Run PowerShell command to get apps
            cmd = ["powershell", "-NoProfile", "-Command", ps_script]
            # Use distinct encoding to avoid issues
            result = subprocess.run(cmd, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if '|' in line:
                    name, target = line.split('|', 1)
                    apps[name.strip()] = target.strip()
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
            cmd = system_apps.get(app_entry, app_entry)
            
            try:
                print(f"Launching: {cmd}")
                if self.os_type == "Windows":
                    # On Windows, using Popen with shell=False is often better for executables,
                    # but if it's a command string, shell=True. 
                    # start_new_session equivalent is creationflags=subprocess.CREATE_NEW_CONSOLE
                    # subprocess.DETACHED_PROCESS = 0x00000008
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
        
        for proc in self.running_processes:
            try:
                if self.os_type == "Windows":
                    # Windows: terminate() usually works, or taskkill /F /T /PID
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], 
                                   capture_output=True)
                else:
                    # Linux/macOS: Send SIGTERM to the process group
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception as e:
                print(f"Error terminating process {proc.pid}: {e}")
        
        self.running_processes = []
        return True

    def get_workspace_names(self):
        self.load_workspaces() # Sync
        return list(self.workspaces.keys())

    def get_workspace_apps(self, name):
        self.load_workspaces() # Sync
        return self.workspaces.get(name, [])
