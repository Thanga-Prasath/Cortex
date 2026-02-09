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
        # Placeholder for Linux
        return [{"name": "Linux App Support Pending", "version": "0.1", "size": "0 MB"}]

    def _get_mac_apps(self):
        # Placeholder for macOS
        return [{"name": "macOS App Support Pending", "version": "0.1", "size": "0 MB"}]

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
        return False, "Not supported on this OS."
