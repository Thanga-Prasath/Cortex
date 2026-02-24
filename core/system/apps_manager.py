import platform
import subprocess
import os
import sys

class AppsManager:
    def __init__(self):
        self.os_type = platform.system()

    def get_installed_apps(self):
        """
        Returns a list of dictionaries containing app details:
        {
            "name": "App Name",
            "version": "1.0.0",
            "size": "100 MB", # Estimated
            "uninstall_string": "...",
            "install_date": "YYYYMMDD",
            "publisher": "..."
        }
        """
        apps = []
        if self.os_type == 'Windows':
            apps = self._get_windows_apps()
        elif self.os_type == 'Linux':
            apps = self._get_linux_apps()
        elif self.os_type == 'Darwin':
            apps = self._get_mac_apps()
        
        # Sort by name
        apps.sort(key=lambda x: x.get('name', '').lower())
        return apps

    def _get_windows_apps(self):
        import winreg
        apps = []
        # Registry keys to search
        uninstall_keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        
        # Roots: HKLM and HKCU
        roots = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]

        for root in roots:
            for key_path in uninstall_keys:
                try:
                    with winreg.OpenKey(root, key_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        
                                        # Skip system components/updates usually usually marked with SystemComponent or missing UninstallString
                                        is_system_component = False
                                        try:
                                            if winreg.QueryValueEx(subkey, "SystemComponent")[0] == 1:
                                                is_system_component = True
                                        except FileNotFoundError:
                                            pass
                                            
                                        if is_system_component:
                                            continue

                                        app_data = {"name": name}
                                        
                                        try:
                                            app_data["version"] = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                        except FileNotFoundError:
                                            app_data["version"] = "Unknown"
                                            
                                        try:
                                            app_data["publisher"] = winreg.QueryValueEx(subkey, "Publisher")[0]
                                        except FileNotFoundError:
                                            app_data["publisher"] = "Unknown"
                                            
                                        try:
                                            app_data["uninstall_string"] = winreg.QueryValueEx(subkey, "UninstallString")[0]
                                        except FileNotFoundError:
                                            app_data["uninstall_string"] = ""
                                            
                                        try:
                                            app_data["quiet_uninstall_string"] = winreg.QueryValueEx(subkey, "QuietUninstallString")[0]
                                        except FileNotFoundError:
                                            app_data["quiet_uninstall_string"] = ""

                                        try:
                                            app_data["modify_path"] = winreg.QueryValueEx(subkey, "ModifyPath")[0]
                                        except FileNotFoundError:
                                            app_data["modify_path"] = ""

                                        try:
                                            size = winreg.QueryValueEx(subkey, "EstimatedSize")[0]
                                            # Size is in KB
                                            app_data["size"] = f"{size / 1024:.2f} MB"
                                        except FileNotFoundError:
                                            app_data["size"] = "-"

                                        apps.append(app_data)
                                    except FileNotFoundError:
                                        continue
                            except OSError:
                                continue
                except OSError:
                    continue
        
        # Deduplicate based on name and version
        unique_apps = {}
        for app in apps:
            key = (app['name'], app['version'])
            if key not in unique_apps:
                unique_apps[key] = app
        
        return list(unique_apps.values())

    def _get_linux_apps(self):
        """
        List installed applications on Linux using available package managers.
        Tries dpkg (Debian/Ubuntu), rpm (Fedora/RHEL), and pacman (Arch) in order.
        """
        import shutil
        
        apps = []
        
        # Strategy 1: dpkg (Debian/Ubuntu/Mint)
        if shutil.which("dpkg-query"):
            try:
                result = subprocess.run(
                    ["dpkg-query", "-W", "-f",
                     "${Package}\\t${Version}\\t${Installed-Size}\\t${Maintainer}\\n"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1] if len(parts) > 1 else "Unknown"
                            
                            # Size from dpkg is in KB
                            size_str = "-"
                            if len(parts) > 2 and parts[2]:
                                try:
                                    size_kb = int(parts[2])
                                    size_str = f"{size_kb / 1024:.2f} MB"
                                except ValueError:
                                    pass
                            
                            publisher = parts[3] if len(parts) > 3 else "Unknown"
                            # Clean publisher (often has email in angle brackets)
                            if '<' in publisher:
                                publisher = publisher.split('<')[0].strip()
                            
                            apps.append({
                                "name": name,
                                "version": version,
                                "size": size_str,
                                "publisher": publisher,
                                "uninstall_string": f"sudo apt remove {name}",
                                "quiet_uninstall_string": f"sudo apt remove -y {name}",
                                "modify_path": ""
                            })
                    return apps
            except (subprocess.TimeoutExpired, Exception) as e:
                print(f"[AppsManager] dpkg-query failed: {e}")
        
        # Strategy 2: rpm (Fedora/RHEL/openSUSE)
        if shutil.which("rpm"):
            try:
                result = subprocess.run(
                    ["rpm", "-qa", "--queryformat",
                     "%{NAME}\\t%{VERSION}-%{RELEASE}\\t%{SIZE}\\t%{VENDOR}\\n"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1] if len(parts) > 1 else "Unknown"
                            
                            size_str = "-"
                            if len(parts) > 2 and parts[2]:
                                try:
                                    size_bytes = int(parts[2])
                                    size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
                                except ValueError:
                                    pass
                            
                            publisher = parts[3] if len(parts) > 3 else "Unknown"
                            
                            # Determine uninstall command based on available tool
                            if shutil.which("dnf"):
                                uninstall_cmd = f"sudo dnf remove {name}"
                            elif shutil.which("yum"):
                                uninstall_cmd = f"sudo yum remove {name}"
                            else:
                                uninstall_cmd = f"sudo rpm -e {name}"
                            
                            apps.append({
                                "name": name,
                                "version": version,
                                "size": size_str,
                                "publisher": publisher,
                                "uninstall_string": uninstall_cmd,
                                "quiet_uninstall_string": f"{uninstall_cmd} -y",
                                "modify_path": ""
                            })
                    return apps
            except (subprocess.TimeoutExpired, Exception) as e:
                print(f"[AppsManager] rpm failed: {e}")
        
        # Strategy 3: pacman (Arch/Manjaro)
        if shutil.which("pacman"):
            try:
                result = subprocess.run(
                    ["pacman", "-Q"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1]
                            
                            apps.append({
                                "name": name,
                                "version": version,
                                "size": "-",
                                "publisher": "Unknown",
                                "uninstall_string": f"sudo pacman -R {name}",
                                "quiet_uninstall_string": f"sudo pacman -R --noconfirm {name}",
                                "modify_path": ""
                            })
                    return apps
            except (subprocess.TimeoutExpired, Exception) as e:
                print(f"[AppsManager] pacman failed: {e}")
        
        return apps

    def _get_mac_apps(self):
        """
        List installed applications on macOS using system_profiler.
        """
        import json as json_mod
        apps = []
        
        try:
            result = subprocess.run(
                ["system_profiler", "SPApplicationsDataType", "-json"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                data = json_mod.loads(result.stdout)
                app_list = data.get("SPApplicationsDataType", [])
                
                for app in app_list:
                    name = app.get("_name", "Unknown")
                    version = app.get("version", "Unknown")
                    path = app.get("path", "")
                    
                    # Estimate size from path if available
                    size_str = "-"
                    obtained_from = app.get("obtained_from", "Unknown")
                    
                    apps.append({
                        "name": name,
                        "version": version,
                        "size": size_str,
                        "publisher": obtained_from,
                        "uninstall_string": f"rm -rf '{path}'" if path else "",
                        "quiet_uninstall_string": "",
                        "modify_path": ""
                    })
        except (subprocess.TimeoutExpired, Exception) as e:
            print(f"[AppsManager] macOS system_profiler failed: {e}")
        
        return apps

    def uninstall_app(self, app_data):
        """
        Launches the uninstaller for the given app.
        """
        if self.os_type == 'Windows':
            cmd = app_data.get("quiet_uninstall_string") or app_data.get("uninstall_string")
            if cmd:
                # Some uninstall strings are quoted, some are not. 
                # Subprocess Popen is preferred.
                try:
                    subprocess.Popen(cmd, shell=True)
                    return True, "Uninstaller started."
                except Exception as e:
                    return False, str(e)
            else:
                return False, "No uninstall command found."
        
        elif self.os_type == 'Linux':
            cmd = app_data.get("uninstall_string", "")
            if cmd:
                try:
                    # Open in a terminal so user can see progress and enter sudo password
                    import shutil
                    terminal = None
                    for t in ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]:
                        if shutil.which(t):
                            terminal = t
                            break
                    
                    if terminal == "gnome-terminal":
                        subprocess.Popen(f'gnome-terminal -- bash -c "{cmd}; read -p Press_Enter..."', shell=True)
                    elif terminal == "konsole":
                        subprocess.Popen(f'konsole -e bash -c "{cmd}; read -p Press_Enter..."', shell=True)
                    else:
                        subprocess.Popen(f'xterm -e bash -c "{cmd}; read"', shell=True)
                    
                    return True, "Uninstaller started in terminal."
                except Exception as e:
                    return False, str(e)
            return False, "No uninstall command found."
        
        return False, "Not supported on this OS."

    def repair_app(self, app_data):
        """
        Launches repair or modify command.
        """
        if self.os_type == 'Windows':
            cmd = app_data.get("modify_path")
            uninstall_string = app_data.get("uninstall_string", "")
            
            # Special handling for MSI
            # If UninstallString is MsiExec, we can often force a repair
            if "msiexec.exe" in uninstall_string.lower() and "/i" in uninstall_string.lower():
                # Replace install flag /I with repair flag /fa (force repair all)
                # or just /f if it's a standard package
                # Use regex or simple replace, ensuring casing handling if valid
                # Simple replace might miss if /I is /i. 
                # Let's reconstruct the command carefully if possible, or just replace /I and /i
                repair_cmd = uninstall_string.replace("/I", "/fa").replace("/i", "/fa")
                try:
                    subprocess.Popen(repair_cmd, shell=True)
                    return True, "MSI Repair started."
                except Exception as e:
                    return False, str(e)
            
            # If we have a ModifyPath
            if cmd:
                # Check if ModifyPath is identical to UninstallString and not MSI
                # If they are identical, it's likely just the uninstaller
                if cmd.lower().strip('"') == uninstall_string.lower().strip('"'):
                     return False, "Repair command is identical to Uninstall."

                try:
                    subprocess.Popen(cmd, shell=True)
                    return True, "Repair/Modify started."
                except Exception as e:
                    return False, str(e)
            
            return False, "No specific repair command found."
        
        elif self.os_type == 'Linux':
            # On Linux, the closest to "repair" is reinstalling the package
            name = app_data.get("name", "")
            if name:
                import shutil
                if shutil.which("apt"):
                    repair_cmd = f"sudo apt install --reinstall {name}"
                elif shutil.which("dnf"):
                    repair_cmd = f"sudo dnf reinstall {name}"
                elif shutil.which("pacman"):
                    repair_cmd = f"sudo pacman -S {name}"
                else:
                    return False, "No supported package manager found."
                
                try:
                    terminal = None
                    for t in ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]:
                        if shutil.which(t):
                            terminal = t
                            break
                    
                    if terminal == "gnome-terminal":
                        subprocess.Popen(f'gnome-terminal -- bash -c "{repair_cmd}; read -p Press_Enter..."', shell=True)
                    else:
                        subprocess.Popen(f'xterm -e bash -c "{repair_cmd}; read"', shell=True)
                    
                    return True, "Reinstall started in terminal."
                except Exception as e:
                    return False, str(e)
            return False, "No package name available."
        
        return False, "Not supported on this OS."
