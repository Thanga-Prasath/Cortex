import platform
import os
from components.system.custom_utils import run_in_separate_terminal, get_cmd_with_auto_install
from core.runtime_path import get_app_root

import subprocess

# Import dependency manager for auto-installing antivirus tools
try:
    from core.utils.dependency_manager import ensure_commands, get_dependency_manager
    _HAS_DEPENDENCY_MANAGER = True
except ImportError:
    _HAS_DEPENDENCY_MANAGER = False
    print("[Warning] Dependency manager not available for security scan")

def run_security_scan(speaker=None):
    os_type = platform.system()
    
    if speaker:
        speaker.speak("Checking system security status...", blocking=True)
    
    if os_type == 'Linux':
        # Check for rkhunter first (rootkit hunter)
        if os.system("which rkhunter > /dev/null 2>&1") == 0:
            run_in_separate_terminal('sudo rkhunter --check --sk', "SECURITY SCAN", os_type, speaker)
        else:
            # Use ClamAV as fallback - ensure it's installed
            if _HAS_DEPENDENCY_MANAGER:
                # Check if clamscan is available
                dm = get_dependency_manager()
                if not dm.is_command_available('clamscan'):
                    if speaker:
                        speaker.speak("ClamAV antivirus is not installed. Installing it now...")
                    
                    print("[Security] clamscan not found. Opening terminal to install ClamAV...")
                    print("[Security] A terminal window will open - please enter your password")
                    
                    # Install clamav package (terminal window will open automatically)
                    # Note: package is 'clamav' but command is 'clamscan'
                    if dm.install_linux_package('clamav', command_name='clamscan'):
                        print("[Security] ✅ ClamAV installed successfully")
                        
                        # Update virus database (important for first-time use)
                        # This may also need terminal access for first-time setup
                        if speaker:
                            speaker.speak("Updating virus database. This may take a moment...")
                        
                        print("[Security] Updating virus database...")
                        try:
                            # Run freshclam in terminal so user can see progress
                            terminal_commands = [
                                f"gnome-terminal -- bash -c 'sudo freshclam; echo; echo \"Database update complete. Press Enter to close...\"; read'",
                                f"konsole -e bash -c 'sudo freshclam; echo; echo \"Database update complete. Press Enter to close...\"; read'",
                                f"xterm -e 'bash -c \"sudo freshclam; echo; echo Database update complete. Press Enter to close...; read\"'",
                            ]
                            
                            terminal_opened = False
                            for terminal_cmd in terminal_commands:
                                try:
                                    subprocess.Popen(terminal_cmd, shell=True)
                                    terminal_opened = True
                                    print("[Security] Terminal opened for virus database update")
                                    break
                                except:
                                    continue
                            
                            if not terminal_opened:
                                # Fallback: try in background
                                subprocess.run(['sudo', 'freshclam'], 
                                             check=False, 
                                             timeout=120,
                                             stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL)
                            
                            print("[Security] ✅ Virus database updated")
                        except:
                            print("[Security] ⚠️  Could not update virus database automatically")
                        
                        if speaker:
                            speaker.speak("ClamAV installed successfully. Starting security scan.")
                    else:
                        if speaker:
                            speaker.speak("Could not install ClamAV. Please check the terminal window or install manually.")
                        print("[Security] ❌ Failed to install ClamAV")
                        print("[Security] Install manually: sudo apt install clamav")
                        return
                
                # Run the scan
                run_in_separate_terminal('clamscan -r ~', "SECURITY SCAN", os_type, speaker)
            else:
                # No dependency manager - just try to run it
                run_in_separate_terminal('clamscan -r ~', "SECURITY SCAN", os_type, speaker)
            
    elif os_type == 'Windows':
        # SMART CHECK: Check SecurityCenter2 for ANY active antivirus (including 3rd party)
        try:
            # Get AV products from WMI/CIM
            # [FIX] Added -NoProfile to prevent user profile output (like venv activation) from messing up JSON parsing
            cmd = "powershell -NoProfile \"Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object -Property displayName | ConvertTo-Json\""
            result = subprocess.check_output(cmd, shell=True).decode().strip()
            
            # Helper to parse JSON output which might be a list or single object
            import json
            try:
                if not result:
                     av_list = []
                elif result.startswith('['):
                     av_list = json.loads(result)
                else:
                     av_list = [json.loads(result)]
            except json.JSONDecodeError:
                # Fallback implementation if JSON fails (rare)
                av_list = []

            # Filter for active AVs
            detected_avs = [av['displayName'] for av in av_list if 'displayName' in av]
            
            non_defender_avs = [name for name in detected_avs if "Windows Defender" not in name]
            
            if non_defender_avs:
                # 3rd Party AV Detected
                av_name = non_defender_avs[0]
                speaker.speak(f"System is protected by {av_name}. Can't do automated system scan with third party antivirus system, user action needed.")
                
                # Smart Dispatcher for known AVs
                if "Bitdefender" in av_name:
                    # Attempt to open Bitdefender UI
                    scan_paths = [
                        r"C:\Program Files\Bitdefender\Bitdefender Security\bdagent.exe",
                        r"C:\Program Files\Bitdefender\Bitdefender Security\seccenter.exe"
                    ]
                    found_gui = False
                    for path in scan_paths:
                        if os.path.exists(path):
                            speaker.speak("Opening Bitdefender interface...")
                            subprocess.Popen(f'"{path}"', shell=True)
                            found_gui = True
                            break
                    
                    if not found_gui:
                        speaker.speak("Opening security dashboard.")
                        subprocess.Popen("start windowsdefender:", shell=True)

                else:
                    # Universal Fallback for other AVs (Norton, McAfee, etc.)
                    speaker.speak("Opening security dashboard.")
                    subprocess.Popen("start windowsdefender:", shell=True)

            elif "Windows Defender" in detected_avs:
                # Only Defender found, verify it's actually ON
                # [FIX] Use JSON output for robustness AND -NoProfile
                cmd_status = "powershell -NoProfile \"Get-MpComputerStatus | Select-Object -Property AntivirusEnabled,RealTimeProtectionEnabled | ConvertTo-Json\""
                try:
                    res_status = subprocess.check_output(cmd_status, shell=True).decode().strip()
                    status_json = json.loads(res_status)
                    
                    # Handle case where ConvertTo-Json might return a single object or list
                    if isinstance(status_json, list):
                        status_json = status_json[0]
                        
                    av_enabled = status_json.get('AntivirusEnabled', False)
                    # RealTimeProtection might be off but scanning still works, but let's check AV enabled.

                    if av_enabled:
                         speaker.speak("Starting a Quick Scan with Windows Defender...")
                         
                         # Launch PyQt6 GUI for scanning
                         # Using sys.executable to ensure we use the same python interpreter (virtualenv)
                         import sys
                         gui_script = os.path.abspath(os.path.join("components", "system", "scan_gui.py"))
                         
                         if os.path.exists(gui_script):
                             # Run detached to not block
                             subprocess.Popen([sys.executable, gui_script], cwd=get_app_root())
                         else:
                             speaker.speak("Scan GUI not found. Falling back to dashboard.")
                             subprocess.Popen("start windowsdefender:", shell=True)
                    else:
                         speaker.speak("Warning. Windows Defender appears to be disabled. Opening security settings.")
                         subprocess.Popen("start windowsdefender:", shell=True)
                except Exception as e:
                    print(f"Error parsing Defender status: {e}")
                    speaker.speak("Windows Defender is present but I cannot verify its status. Opening security settings.")
                    subprocess.Popen("start windowsdefender:", shell=True)

            else:
                # No AV found at all
                speaker.speak("Critical Warning. No antivirus software detected on this system. Opening security settings.")
                subprocess.Popen("start windowsdefender:", shell=True)
                
        except Exception as e:
             print(f"Security Check Error: {e}")
             speaker.speak("I could not verify the security status. Opening Windows Security.")
             subprocess.Popen("start windowsdefender:", shell=True)
        
    elif os_type == 'Darwin': 
        # MacOS placeholder
        mac_cmd = 'echo "Gatekeeper Status:"; spctl --status; echo ""; echo "System Integrity Protection:"; csrutil status'
        run_in_separate_terminal(mac_cmd, "SECURITY STATUS", os_type, speaker)

