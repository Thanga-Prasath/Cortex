import platform
import os
import subprocess
import sys

# Import new system components
from components.system import (
    wifi, apps, update, cpu, temperature, user, compression, services, dns,
    info, console, ip, memory, disk, directory, security, ports, firewall,
    connections, processes, login, traffic, speedtest, cleanup, kill
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
        elif tag == 'system_ip':
            ip.get_ip_address(self.speaker)
            return True
        elif tag == 'system_memory':
            memory.check_memory(self.speaker)
            return True
        elif tag == 'system_disk':
            disk.check_disk(self.speaker)
            return True
        elif tag == 'list_curr_dir':
            directory.list_files(self.speaker)
            return True
        elif tag == 'system_scan':
            security.run_security_scan(self.speaker)
            return True
        elif tag == 'check_ports':
            ports.check_ports(self.speaker)
            return True
        elif tag == 'check_firewall':
            firewall.check_firewall(self.speaker)
            return True
        elif tag == 'check_connections':
            connections.check_connections(self.speaker)
            return True
        elif tag == 'system_processes':
            processes.check_processes(self.speaker)
            return True
        elif tag == 'login_history':
            login.check_login_history(self.speaker)
            return True
        elif tag == 'network_traffic':
            traffic.check_network_traffic(self.speaker)
            return True
        elif tag == 'internet_speed':
            speedtest.check_internet_speed(self.speaker)
            return True
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
        elif tag == 'system_services':
            services.manage_system_services(self.speaker)
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
            
        return False

    def _print_header(self, title):
        print(f"\n{'='*40}")
        print(f" {title.center(38)}")
        print(f"{'='*40}")
