import platform
import os
import subprocess
import sys

# Import new system components
from components.system import (
    wifi, apps, update, cpu, temperature, user, compression, services, dns,
    info, console, ip, memory, disk, directory, security, ports, firewall,
    connections, processes, login, traffic, cleanup, kill,
    uptime, battery, recycle_bin, screenshot, audio, wifi_password, hidden_files, awake, dark_mode,
    tools, power, volume
)

class SystemEngine:
    def __init__(self, speaker, listener=None):
        self.speaker = speaker
        self.listener = listener
        self.os_type = platform.system()

    def handle_intent(self, tag, command=""):
        if tag == 'system_info':
            info.system_info(self.speaker)
            return True
        elif tag == 'console_clear':
            console.clear_console(self.speaker)
            return True

        elif tag == 'system_memory':
            memory.check_memory(self.speaker)
            return True
        elif tag == 'system_disk':
            if any(k in command.lower() for k in ['format', 'repair', 'scan', 'list']):
                return False
            disk.check_disk(self.speaker)
            return True
        elif tag == 'list_curr_dir':
            directory.list_files(self.speaker)
            return True
        elif tag == 'system_scan':
            security.run_security_scan(self.speaker)
            return True
        elif tag == 'scan_drivers':
            self.speaker.speak("Opening Driver Manager.")
            try:
                # Launch the GUI as a separate process
                subprocess.Popen([sys.executable, "-m", "core.ui.driver_window"])
            except Exception as e:
                self.speaker.speak(f"Failed to open driver manager: {e}")
                print(f"Error launching driver window: {e}")
            return True

        elif tag == 'check_firewall':
            firewall.check_firewall(self.speaker)
            return True
        elif tag == 'check_connections':
            connections.check_connections(self.speaker)
            return True

        elif tag == 'login_history':
            login.check_login_history(self.speaker)
            return True
        elif tag == 'network_traffic':
            if any(k in command.lower() for k in ['ping', 'speed', 'test', 'latency']):
                return False
            traffic.check_network_traffic(self.speaker)
            return True
        # elif tag == 'internet_speed':
        #     # speedtest.check_internet_speed(self.speaker)
        #     self.speaker.speak("Speed test module is currently unavailable.")
        #     return True
        elif tag == 'system_cleanup':
            cleanup.clean_system(self.speaker)
            return True
        elif tag == 'kill_process':
            kill.kill_process(command, self.speaker, self.listener)
            return True
            
        # New System Functions
        elif tag == 'wifi_list':
            wifi.get_wifi_list(self.speaker)
            return True
        elif tag == 'list_apps':
            apps.list_installed_apps(self.speaker)
            return True
        elif tag == 'system_update':
            update.check_for_updates(self.speaker)
            return True
        elif tag == 'cpu_info':
            cpu.get_cpu_info(self.speaker)
            return True
        elif tag == 'system_temp':
            temperature.get_system_temperature(self.speaker)
            return True
        elif tag == 'current_user':
            user.get_current_user(self.speaker)
            return True

        elif tag == 'clear_dns':
            dns.clear_dns_cache(self.speaker)
            return True
        elif tag == 'file_compress':
            # Basic stub: asking for file would be handled inside if we passed speaker/listener
            # But for now, let's just trigger it. 
            # ideally we need to parse command or ask user.
            # compression.compress_file(..., speaker=self.speaker)
            self.speaker.speak("Compression is not yet fully interactive via voice.")
            return True
        elif tag == 'file_extract':
            self.speaker.speak("Extraction is not yet fully interactive via voice.")
            return True
            
        # New Feature Handlers
        elif tag == 'system_uptime':
            uptime.get_system_uptime(self.speaker)
            return True
        elif tag == 'check_battery':
            if any(k in command.lower() for k in ['cycle', 'health', 'report']):
                return False # Let Dynamic/Brain handle it
            battery.check_battery_status(self.speaker)
            return True
        elif tag == 'empty_bin':
            recycle_bin.empty_recycle_bin(self.speaker)
            return True
        elif tag == 'take_screenshot':
            screenshot.take_screenshot(self.speaker)
            return True
        elif tag == 'restart_audio':
            audio.restart_audio_service(self.speaker)
            return True

        # Round 2 Features
        elif tag == 'wifi_password':
            self.speaker.speak("Retrieving Wi-Fi info.")
            gui_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "core", "ui", "wifi_password_gui.py")
            
            try:
                if platform.system() == 'Windows':
                     subprocess.Popen([sys.executable, gui_script], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                     subprocess.Popen([sys.executable, gui_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                self.speaker.speak(f"Failed to open Wi-Fi GUI: {e}")
                # Fallback to speech
                wifi_password.report_wifi_password(self.speaker)
                
            return True

        elif tag == 'toggle_hidden_files':
            # Basic toggle logic based on command pattern could be added,
            # but for now we'll just toggle state (smart nlu contexts can be added later)
            if "show" in command or "reveal" in command:
                hidden_files.toggle_hidden_files(self.speaker, show=True)
            elif "hide" in command:
                hidden_files.toggle_hidden_files(self.speaker, show=False)
            else:
                hidden_files.toggle_hidden_files(self.speaker, show=None) # Toggle
            return True
        elif tag == 'keep_awake':
            awake.enable_keep_awake(self.speaker)
            return True
        elif tag == 'stop_keep_awake':
            awake.disable_keep_awake(self.speaker)
            return True
        elif tag == 'toggle_dark_mode':
            dark_mode.toggle_dark_mode(self.speaker)
            return True
        
        # Round 3: Tools
        elif tag == 'open_task_manager':
            tools.open_task_manager(self.speaker)
            return True
        elif tag == 'open_control_panel':
            tools.open_control_panel(self.speaker)
            return True
        elif tag == 'open_terminal':
            tools.open_terminal(self.speaker)
            return True
        elif tag == 'open_msconfig':
            tools.open_system_config(self.speaker)
            return True
        elif tag == 'open_device_manager':
            tools.open_device_manager(self.speaker)
            return True
        elif tag == 'open_registry_editor':
            tools.open_registry_editor(self.speaker)
            return True

        # Round 4: Power & System Management
        elif tag == 'system_lock':
            power.lock_screen(self.speaker)
            return True
        elif tag == 'system_sleep':
            power.sleep_system(self.speaker)
            return True
        elif tag == 'system_restart':
            power.restart_system(self.speaker, self.listener)
            return True
        elif tag == 'system_shutdown':
            power.shutdown_system(self.speaker, self.listener)
            return True
            
        elif tag == 'volume_mute':
            volume.mute_volume(self.speaker)
            return True
        elif tag == 'volume_unmute':
            volume.unmute_volume(self.speaker)
            return True
        elif tag == 'volume_set':
            # Basic volume setting (defaulting to 50 if not specified for now, 
            # ideally we parse numbers from command in a helper)
            import re
            numbers = re.findall(r'\d+', command)
            if numbers:
                volume.set_volume(numbers[0], self.speaker)
            else:
                self.speaker.speak("To set volume, please say set volume to a percentage, like set volume to 50.")
            return True
            
        elif tag == 'clear_dns':
            dns.clear_dns_cache(self.speaker)
            return True
        elif tag == 'system_services':
            self.speaker.speak("Opening System Services Manager.")
            gui_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "core", "ui", "services_window.py")
            
            try:
                if os.name == 'nt':
                     subprocess.Popen([sys.executable, gui_script], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                     # Fallback for Linux/macOS
                     services.manage_system_services(self.speaker)
            except Exception as e:
                self.speaker.speak(f"Failed to open services manager: {e}")
                
            return True
            
        elif tag == 'repair_permissions':
            self.speaker.speak("Starting permission repair script. This will open in a separate terminal.")
            from components.system.custom_utils import run_in_separate_terminal
            run_in_separate_terminal(f"sudo {os.path.join(os.getcwd(), 'scripts', 'sunday-permissions.sh')}", "PERMISSION REPAIR", self.os_type, self.speaker)
            return True
            
        return False

    def _print_header(self, title):
        print(f"\n{'='*40}")
        print(f" {title.center(38)}")
        print(f"{'='*40}")
