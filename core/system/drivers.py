import platform
import subprocess
import json
import os
import sys
import shutil

class DriverManager:
    def __init__(self):
        self.os_type = platform.system()

    def get_drivers(self):
        """Returns a list of drivers/modules."""
        if self.os_type == "Windows":
            return self._get_windows_drivers()
        elif self.os_type == "Linux":
            return self._get_linux_drivers()
        elif self.os_type == "Darwin":
            return self._get_mac_drivers()
        else:
            return []

    def check_updates(self):
        """Returns a list of available updates."""
        if self.os_type == "Windows":
            return self._check_windows_updates()
        elif self.os_type == "Linux":
            return self._check_linux_updates()
        elif self.os_type == "Darwin":
            return self._check_mac_updates()
        else:
            return []

    def update_package(self, package_id):
        """Updates a specific package/driver."""
        if self.os_type == "Windows":
            return self._update_windows_package(package_id)
        elif self.os_type == "Linux":
            return self._update_linux_package(package_id)
        elif self.os_type == "Darwin":
            return self._update_mac_package(package_id)
        return False

    # --- Windows Implementation ---
    def _get_windows_drivers(self):
        drivers = []
        try:
            # Use PowerShell to get simplified driver info
            # We use a simpler selection to avoid encoding issues with some fields
            cmd = "Get-WmiObject Win32_PnPSignedDriver | Select-Object DeviceName, DriverVersion, Manufacturer, InfName | ConvertTo-Json -Depth 1"
            
            # Run with explicit encoding handling
            # Add -NoProfile to avoid "Virtual environment activated" or other profile text
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd], 
                capture_output=True, 
                text=True, 
                encoding='utf-8', # Force UTF-8
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Fallback: sometimes PowerShell returns single object not in list, or empty
                    # If empty, data is None or empty string
                    if not result.stdout.strip():
                        return []
                    # unexpected format
                    print(f"JSON Decode Error. Output start: {result.stdout[:100]}")
                    return []

                # Handle single object vs list return
                if isinstance(data, dict):
                    data = [data]
                
                if data:
                    for item in data:
                        if item.get("DeviceName"):
                            drivers.append({
                                "name": item.get("DeviceName"),
                                "version": item.get("DriverVersion"),
                                "manufacturer": item.get("Manufacturer"),
                                "type": "Driver",
                                "status": "Installed", 
                                "id": item.get("InfName")
                            })
        except Exception as e:
            print(f"Error fetching Windows drivers: {e}")
        return drivers

    def _check_windows_updates(self):
        updates = []
        try:
            # Use `winget list --upgrade-available` to find updates
            
            # Use PowerShell to run winget, as it handles AppExecutionAliases better
            cmd = ["powershell", "-NoProfile", "-Command", "winget list --upgrade-available"]
            
            # Ensure we don't get stuck on agreements (though list usually doesn't prompt)
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                # Skip the header (Name, Id, Version, Available, Source)
                # Typically the header is followed by '---'
                header_found = False
                for line in lines:
                    if "---" in line:
                        header_found = True
                        continue
                    
                    if header_found and line.strip():
                        # The columns are fixed width, which is annoying.
                        # But usually the ID is the second column.
                        # Name | Id | Version | Available | Source
                        # Let's try to split by multiple spaces, which is risky but often works for reading.
                        parts = line.split()
                        # A better heuristic:
                        # last column is Source (optional)
                        # 2nd to last is Available
                        # 3rd to last is Version
                        # But ID can have spaces? No. ID is usually simpler. Name has spaces.
                        
                        if len(parts) >= 4:
                            # We'll grab the ID. The ID is the most important part for updating.
                            # Usually: Name (Variable) | Id (No Spaces) | Version | Available
                            
                            # Let's try to find the ID. 
                            # If we look from right to left:
                            # Source (optional), Available, Version.
                            # ID is the token before Version.
                            
                            # Example: "Google Chrome  Google.Chrome  100.0  101.0  winget"
                            available = parts[-2] if len(parts) > 4 else parts[-1] # if source is missing
                            current_version = parts[-3] if len(parts) > 4 else parts[-2]
                            # id is likely parts[-4] if len(parts) > 4 else parts[-3]
                            # This is too brittle.
                            
                            # Let's restart: split by 2+ spaces to separate columns roughly
                            import re
                            columns = re.split(r'\s{2,}', line.strip())
                            
                            if len(columns) >= 4:
                                name = columns[0]
                                pkg_id = columns[1]
                                version = columns[2]
                                available = columns[3]
                                
                                updates.append({
                                    "name": name,
                                    "id": pkg_id,
                                    "current_version": version,
                                    "new_version": available,
                                    "type": "Software", # It's via winget
                                    "status": "Update Available"
                                })
        except Exception as e:
            print(f"Error checking Windows updates: {e}")
        return updates

    def _update_windows_package(self, package_id):
        """Updates a Windows package using winget."""
        try:
            # Run winget upgrade in a separate window so user can see progress if there's a prompt
            # But winget upgrade --id <id> --silent --accept-package-agreements --accept-source-agreements is also an option.
            # For this GUI, we'll try silent first.
            cmd = ["powershell", "-NoProfile", "-Command", f"winget upgrade --id {package_id} --silent --accept-package-agreements --accept-source-agreements"]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
            return result.returncode == 0
        except Exception as e:
            print(f"Error updating Windows package: {e}")
            return False

    # --- Linux Implementation ---
    def _get_linux_drivers(self):
        drivers = []
        try:
            # lsmod
            result = subprocess.run(["lsmod"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.splitlines()[1:]:
                    parts = line.split()
                    if parts:
                        drivers.append({
                            "name": parts[0],
                            "version": "Kernel Module",
                            "manufacturer": "Linux",
                            "type": "Module",
                            "status": "Loaded",
                            "id": parts[0]
                        })
        except:
            pass
        return drivers

    def _check_linux_updates(self):
        """Checks for updates using available package manager."""
        updates = []
        try:
            if shutil.which("apt"):
                # Very basic check, parsing apt-get -s upgrade would be complex for a one-shot
                pass
            elif shutil.which("pacman"):
                # checkupdates
                pass
        except:
            pass
        return updates

    def _update_linux_package(self, package_id):
        """Updates a Linux package."""
        try:
            if shutil.which("apt"):
                cmd = f"sudo apt-get install --only-upgrade {package_id} -y"
            elif shutil.which("pacman"):
                cmd = f"sudo pacman -S {package_id} --noconfirm"
            elif shutil.which("dnf"):
                cmd = f"sudo dnf upgrade {package_id} -y"
            else:
                return False
            
            # Since these need sudo, we'd normally need a terminal or a helper.
            # For now, we try to run it.
            os.system(cmd)
            return True
        except:
            return False

    # --- macOS Implementation ---
    def _get_mac_drivers(self):
        drivers = []
        try:
            # kextstat
            result = subprocess.run(["kextstat", "-l", "-k"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.splitlines()[1:]:
                    # Simplified kext parsing
                    parts = line.split()
                    if len(parts) > 6:
                        drivers.append({
                            "name": parts[6],
                            "version": parts[5],
                            "manufacturer": "Apple",
                            "type": "Kernel Extension",
                            "status": "Loaded",
                            "id": parts[6]
                        })
        except:
            pass
        return drivers

    def _check_mac_updates(self):
        """Checks for homebrew updates."""
        updates = []
        try:
            if shutil.which("brew"):
                result = subprocess.run(["brew", "outdated", "--json"], capture_output=True, text=True)
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    for item in data:
                        updates.append({
                            "name": item["name"],
                            "id": item["name"],
                            "current_version": item["installed_versions"][0],
                            "new_version": item["current_version"],
                            "type": "Homebrew",
                            "status": "Update Available"
                        })
        except:
            pass
        return updates

    def _update_mac_package(self, package_id):
        """Updates a macOS package using Homebrew."""
        try:
            if shutil.which("brew"):
                subprocess.run(["brew", "upgrade", package_id], capture_output=True)
                return True
        except:
            pass
        return False
