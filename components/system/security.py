import platform
import os
from components.system.custom_utils import run_in_separate_terminal, get_cmd_with_auto_install

def run_security_scan(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Initiating system security scan.", blocking=False)
    
    if os_type == 'Linux':
            # Prefer rkhunter, then clamav, auto-install rkhunter if neither
            if os.system("which rkhunter > /dev/null 2>&1") == 0:
                run_in_separate_terminal('sudo rkhunter --check --sk', "SECURITY SCAN", os_type, speaker)
            elif os.system("which clamscan > /dev/null 2>&1") == 0:
                run_in_separate_terminal('clamscan -r ~', "SECURITY SCAN (ClamAV)", os_type, speaker)
            else:
                # If neither, try to install rkhunter
                cmd = get_cmd_with_auto_install('rkhunter', 'rkhunter')
                # Need sudo for rkhunter check 
                if 'sudo apt install' in cmd:
                    # Helper returns raw command name at end, we need flags
                    # This is a bit complex for the helper, so we construct manually for this complex case
                    cmd = "echo 'Installing rkhunter...'; sudo apt install rkhunter -y; sudo rkhunter --propupd; sudo rkhunter --check --sk"
                    run_in_separate_terminal(cmd, "SECURITY SCAN (Installing...)", os_type, speaker)
                else: 
                    # Should not happen given logic above, but fallback
                    run_in_separate_terminal('sudo rkhunter --check --sk', "SECURITY SCAN", os_type, speaker)
            
    elif os_type == 'Windows':
        # Windows Defender Scan (using PowerShell for reliability)
        # MpCmdRun.exe path can vary, but Start-MpScan is standard on Win10/11
        ps_cmd = "Start-MpScan -ScanType QuickScan"
        run_in_separate_terminal(f"powershell -Command \"{ps_cmd}\"", "WINDOWS DEFENDER SCAN", os_type, speaker, admin=True)
        
    elif os_type == 'Darwin': # MacOS
        # Check Gatekeeper and SIP status
        mac_cmd = 'echo "Gatekeeper Status:"; spctl --status; echo ""; echo "System Integrity Protection:"; csrutil status'
        run_in_separate_terminal(mac_cmd, "SECURITY STATUS", os_type, speaker)
