import platform
from components.system.custom_utils import run_in_separate_terminal

def get_wifi_list(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Scanning for available Wi-Fi networks.", blocking=False)
    
    if os_type == 'Linux':
        cmd = "nmcli dev wifi list"
        run_in_separate_terminal(cmd, "WI-FI NETWORKS", os_type, speaker)
    elif os_type == 'Windows':
        cmd = "netsh wlan show networks mode=bssid"
        run_in_separate_terminal(cmd, "WI-FI NETWORKS", os_type, speaker)
    elif os_type == 'Darwin':
        cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s"
        run_in_separate_terminal(cmd, "WI-FI NETWORKS", os_type, speaker)
