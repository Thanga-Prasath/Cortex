import platform
from components.system.custom_utils import run_in_separate_terminal

def check_internet_speed(speaker=None):
    os_type = platform.system()
    if speaker:
        speaker.speak("Running internet speed test.", blocking=False)
        
    if os_type == 'Linux':
        # Fix 403 Error: Download latest script directly from GitHub
        # This bypasses the broken apt/pip versions entirely.
        cmd = (
            "echo 'Downloading latest speedtest-cli...'; "
            "curl -L https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -o /tmp/speedtest.py "
            "|| wget https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -O /tmp/speedtest.py; "
            "echo 'Running Speedtest...'; "
            "python3 /tmp/speedtest.py --secure"
        )
        run_in_separate_terminal(cmd, "SPEED TEST", os_type, speaker)
    elif os_type == 'Darwin':
            # Brew install speedtest-cli? Or just networkQuality (native)
            run_in_separate_terminal('networkQuality', "SPEED TEST", os_type, speaker)
    elif os_type == 'Windows':
            # Invoke-WebRequest usually not great for visuals, maybe just ping?
            # Or try to run fast.com in browser?
            # Let's try simple ping for now or check if speedtest cli exists
            run_in_separate_terminal('ping 8.8.8.8 -t', "PING TEST (Latency)", os_type, speaker)
