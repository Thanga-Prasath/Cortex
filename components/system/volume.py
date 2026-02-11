import platform
import subprocess
import os
import shutil

def _run_command(cmd):
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def set_volume(level, speaker):
    try:
        level = int(level)
        level = max(0, min(100, level))
    except ValueError:
        speaker.speak("Please specify a volume level between 0 and 100.")
        return

    speaker.speak(f"Setting volume to {level} percent.")
    os_type = platform.system()

    if os.name == 'nt':
        # Absolute Volume Hack for Windows using SendKeys
        # 174 is Volume Down, 175 is Volume Up.
        # We go down to 0, then up to the level.
        # Each tick is 2 units.
        down_ticks = 100
        up_ticks = int(level / 2)
        
        ps_cmd = f"""
$w = New-Object -ComObject WScript.Shell
for($i=0; $i -lt {down_ticks}; $i++) {{ $w.SendKeys([char]174) }}
for($i=0; $i -lt {up_ticks}; $i++) {{ $w.SendKeys([char]175) }}
"""
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
        
    elif os_type == 'Darwin':
        _run_command(f"osascript -e 'set volume output volume {level}'")
    elif os_type == 'Linux':
        _run_command(f"pactl set-sink-volume @DEFAULT_SINK@ {level}%")

def mute_volume(speaker):
    speaker.speak("Muting audio.")
    if os.name == 'nt':
         subprocess.run(["powershell", "-Command", "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"], capture_output=True)
    elif platform.system() == 'Darwin':
        _run_command("osascript -e 'set volume output muted true'")
    elif platform.system() == 'Linux':
        _run_command("pactl set-sink-mute @DEFAULT_SINK@ 1")

def unmute_volume(speaker):
    speaker.speak("Unmuting audio.")
    if os.name == 'nt':
         subprocess.run(["powershell", "-Command", "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"], capture_output=True)
    elif platform.system() == 'Darwin':
        _run_command("osascript -e 'set volume output muted false'")
    elif platform.system() == 'Linux':
        _run_command("pactl set-sink-mute @DEFAULT_SINK@ 0")
