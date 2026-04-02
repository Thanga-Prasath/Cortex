import threading
import time
import platform
import socket
import subprocess
import psutil

class SystemAutomationEngine:
    def __init__(self, speaker, status_queue=None):
        self.speaker = speaker
        self.status_queue = status_queue
        self.os_type = platform.system()
        self.running = True

        # State tracking
        self.prev_network_state = None
        self.prev_is_plugged = None
        self.prev_bt_count = -1
        
        # Cooldown tracking
        self.last_battery_alert_time = 0
        self.last_battery_alert_type = None

        self.last_bt_check_time = 0

        # Start background loop
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _monitor_loop(self):
        # Initial wait to let system boot / speaker initialize without spamming
        time.sleep(5)
        
        # Initialize initial states quietly to avoid startup spam
        self.prev_network_state = self._check_internet()
        if psutil.sensors_battery():
            self.prev_is_plugged = psutil.sensors_battery().power_plugged
        self.prev_bt_count = self._get_bt_device_count()

        while self.running:
            self._check_network_state()
            self._check_battery_state()
            
            # Check bluetooth less frequently (e.g. every 10 seconds)
            # because some cross-platform CLI calls are slow
            now = time.time()
            if now - self.last_bt_check_time >= 10:
                self._check_bluetooth_state()
                self.last_bt_check_time = now
            
            time.sleep(5)

    def _check_internet(self):
        try:
            # Quick 2-second check if we can reach Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            pass
        return False

    def _get_bt_device_count(self):
        count = 0
        try:
            if self.os_type == 'Linux':
                # 'bluetoothctl devices Connected' outputs one line per connected device
                res = subprocess.run(['bluetoothctl', 'devices', 'Connected'], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    lines = [l for l in res.stdout.strip().split('\n') if l]
                    count = len(lines)
            elif self.os_type == 'Windows':
                # Use powershell to check present bluetooth devices.
                # Exclude the adapter itself by filtering out "Bluetooth Radio" or just look at Count.
                cmd = ["powershell", "-NoProfile", "-Command", 
                       "(Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | Where-Object { $_.Present -eq $true }).Count"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if res.returncode == 0 and res.stdout.strip() != "":
                    try:
                        count = int(res.stdout.strip())
                    except ValueError:
                        pass
            elif self.os_type == 'Darwin':
                res = subprocess.run(['system_profiler', 'SPBluetoothDataType'], capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    count = res.stdout.count("Connected: Yes")
        except Exception as e:
             # Silently ignore errors (e.g. no bluetoothctl)
             pass
        return count

    def _check_network_state(self):
        curr_state = self._check_internet()
        if self.prev_network_state is not None and curr_state != self.prev_network_state:
            # Avoid speaking if dictation might be running, but speaker checks dictation logic where applicable.
            # In Sunday, speaker queue will manage it.
            if curr_state:
                self.speaker.speak("Internet connection established.")
            else:
                self.speaker.speak("Internet connection lost.")
        self.prev_network_state = curr_state

    def _check_bluetooth_state(self):
        curr_count = self._get_bt_device_count()
        if self.prev_bt_count != -1 and curr_count != self.prev_bt_count:
            if curr_count > self.prev_bt_count:
                self.speaker.speak("Bluetooth device connected.")
            else:
                self.speaker.speak("Bluetooth device disconnected.")
        self.prev_bt_count = curr_count

    def _check_battery_state(self):
        battery = psutil.sensors_battery()
        if not battery:
            return  # No battery found (e.g. desktop PC)
        
        percent = battery.percent
        is_plugged = battery.power_plugged
        now = time.time()

        # 1. Charger connection state change
        if self.prev_is_plugged is not None and is_plugged != self.prev_is_plugged:
            if is_plugged:
                self.speaker.speak("Charger connected.")
            else:
                self.speaker.speak("Charger disconnected.")
            # Reset cooldowns on change
            self.last_battery_alert_time = 0 
            self.last_battery_alert_type = None

        self.prev_is_plugged = is_plugged

        # 2. Percentage thresholds
        # Cooldown intervals
        REGULAR_COOLDOWN = 5 * 60  # 5 minutes
        CRITICAL_COOLDOWN = 60     # 1 minute

        alert_type = None
        cooldown = REGULAR_COOLDOWN
        msg = ""

        if is_plugged:
            if percent == 100:
                alert_type = "full"
                msg = "Battery is fully charged. Please disconnect."
                cooldown = CRITICAL_COOLDOWN
            elif percent > 90:
                alert_type = "above90"
                msg = f"Battery is at {percent} percent. Consider disconnecting the charger."
        else:
            if percent <= 5:
                alert_type = "critical"
                msg = f"Battery critically low at {percent} percent."
                cooldown = CRITICAL_COOLDOWN
            elif percent < 30:
                alert_type = "below30"
                msg = f"Battery is below 30 percent. Please connect the charger."

        if alert_type:
            # If state changed, or cooldown has passed for the SAME state
            if alert_type != self.last_battery_alert_type or (now - self.last_battery_alert_time >= cooldown):
                self.speaker.speak(msg)
                self.last_battery_alert_time = now
                self.last_battery_alert_type = alert_type
        else:
            # If we are in normally healthy range (30-90), reset alert tracker
            self.last_battery_alert_type = None

    def shutdown(self):
        self.running = False
