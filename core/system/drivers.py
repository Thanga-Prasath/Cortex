import platform
import subprocess
import json
import os
import sys

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

    # --- Linux Implementation (Placeholder) ---
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
        # apt list --upgradable
        return []

    def _update_linux_package(self, package_id):
        # sudo apt install ...
        return False

    # --- macOS Implementation (Placeholder) ---
    def _get_mac_drivers(self):
        drivers = []
        try:
            # kextstat
            result = subprocess.run(["kextstat", "-l", "-k"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.splitlines()[1:]:
                    # Parse kext output
                    pass
        except:
            pass
        return drivers

    def _check_mac_updates(self):
        # softwareupdate -l
        return []

    def _update_mac_package(self, package_id):
        return False
