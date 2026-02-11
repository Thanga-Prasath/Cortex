import subprocess
import platform
import re

def get_wifi_password(ssid=None):
    """
    Returns the password for the given SSID, or the current connected one if None.
    Returns (ssid, password, error_message).
    """
    os_type = platform.system()
    password = None
    error = None
    current_ssid = ssid
    
    try:
        if os_type == 'Windows':
            # 1. Get current SSID if not provided
            if not current_ssid:
                # parsing "netsh wlan show interfaces"
                out = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], encoding='utf-8', errors='ignore')
                for line in out.split('\n'):
                     if "SSID" in line and "BSSID" not in line:
                         current_ssid = line.split(":")[1].strip()
                         break
            
            if not current_ssid:
                return None, None, "No Wi-Fi connection found."

            # 2. Get Password
            # netsh wlan show profile name="SSID" key=clear
            cmd = ["netsh", "wlan", "show", "profile", f"name={current_ssid}", "key=clear"]
            out = subprocess.check_output(cmd, encoding='utf-8', errors='ignore')
            
            # Parse Key Content
            for line in out.split('\n'):
                if "Key Content" in line:
                    password = line.split(":")[1].strip()
                    break
                    
            if not password:
                 return current_ssid, None, "Password not found or not stored."

        elif os_type == 'Darwin': # macOS
            # 1. Get current SSID
            if not current_ssid:
                out = subprocess.check_output(["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"], encoding='utf-8')
                for line in out.split('\n'):
                    if " SSID:" in line:
                        current_ssid = line.split(":")[1].strip()
                        break
            
            if not current_ssid:
                return None, None, "No Wi-Fi connection found."

            # 2. Get Password using security command (might trigger popup)
            cmd = ["security", "find-generic-password", "-wa", current_ssid]
            password = subprocess.check_output(cmd, encoding='utf-8').strip()

        elif os_type == 'Linux':
             # 1. Get SSID
             if not current_ssid:
                 out = subprocess.check_output(["iwgetid", "-r"], encoding='utf-8').strip()
                 current_ssid = out
             
             if not current_ssid:
                 return None, None, "No Wi-Fi connection found."

             # 2. Get Password (NetworkManager)
             # usually mapped in /etc/NetworkManager/system-connections/ but requires sudo
             # Try nmcli if available
             cmd = f"nmcli -s -g 802-11-wireless-security.psk connection show '{current_ssid}'"
             password = subprocess.check_output(cmd, shell=True, encoding='utf-8').strip()

    except Exception as e:
        error = str(e)
        
    return current_ssid, password, error

def report_wifi_password(speaker):
    ssid, password, error = get_wifi_password()
    
    if error:
        speaker.speak(f"Could not retrieve Wi-Fi password. {error}")
    elif password:
        speaker.speak(f"The password for {ssid} is: {password}")
        # Optional: Spell it out?
    else:
        speaker.speak(f"I found the network {ssid}, but I could not find a saved password.")
