import platform
import os
import subprocess
import sys
from components.application.close_app import close_application




class SystemEngine:
    def __init__(self, speaker, listener=None):
        self.speaker = speaker
        self.listener = listener
        self.os_type = platform.system()

    
    def handle_intent(self, tag, command=""):
        if tag == 'system_info':
            self._report_system_info()
            return True
        elif tag == 'console_clear':
            self._clear_console()
            self.speaker.speak("Console cleared.")
            return True
        elif tag == 'system_ip':
            self._get_ip_address()
            return True
        elif tag == 'system_memory':
            self._check_memory()
            return True
        elif tag == 'system_disk':
            self._check_disk()
            return True
        elif tag == 'list_curr_dir':
            self._list_files()
            return True
        elif tag == 'system_scan':
            self._run_security_scan()
            return True
        elif tag == 'check_ports':
            self._check_ports()
            return True
        elif tag == 'check_firewall':
            self._check_firewall()
            return True
        elif tag == 'check_connections':
            self._check_connections()
            return True
        elif tag == 'system_processes':
            self._check_processes()
            return True
        elif tag == 'login_history':
            self._check_login_history()
            return True
        elif tag == 'network_traffic':
            self._check_network_traffic()
            return True
        elif tag == 'internet_speed':
            self._check_internet_speed()
            return True
        elif tag == 'system_cleanup':
            self._clean_system()
            return True
        elif tag == 'kill_process':
            self._kill_process(command)
            return True
        elif tag == 'system_cleanup':
            self._clean_system()
            return True
        
        return False

    def _get_cmd_with_auto_install(self, command, package):
        """Returns a shell command that tries to install the package if the command is missing (Linux only)."""
        if self.os_type == 'Linux':
            # Check if command exists, if not, try to install
            return f"which {command} > /dev/null 2>&1 || (echo 'Tool {command} not found. Installing {package}...' && sudo apt install {package} -y); {command}"
        return command

    def _print_header(self, title):
        print(f"\n{'='*40}")
        print(f" {title.center(38)}")
        print(f"{'='*40}")

    def _report_system_info(self):
        self.speaker.speak("Opening system information console.", blocking=False)
        
        if self.os_type == 'Linux':
            # Check for neofetch or fastfetch for a pretty output
            if os.system("which fastfetch > /dev/null 2>&1") == 0:
                 self._run_in_separate_terminal('fastfetch', "SYSTEM INFO")
            elif os.system("which neofetch > /dev/null 2>&1") == 0:
                 self._run_in_separate_terminal('neofetch', "SYSTEM INFO")
            else:
                 # Fallback to manual info
                 cmd = (
                     "echo 'OS: ' $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2); "
                     "echo 'Kernel: ' $(uname -r); "
                     "echo 'Uptime: ' $(uptime -p); "
                     "echo 'Memory: ' $(free -h | grep Mem | awk '{print $3 \" / \" $2}'); "
                     "echo 'Disk: '; df -h / | tail -n 1 | awk '{print \"  \" $4 \" free / \" $2 \" total\"}'"
                 )
                 self._run_in_separate_terminal(cmd, "SYSTEM INFO")
                 
        elif self.os_type == 'Windows':
            self._run_in_separate_terminal('systeminfo', "SYSTEM INFO")
            
        elif self.os_type == 'Darwin':
            self._run_in_separate_terminal('system_profiler SPSoftwareDataType SPHardwareDataType', "SYSTEM INFO")

    def _clear_console(self):
        if self.os_type == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
            
    def _run_in_separate_terminal(self, command, title="System Info"):
        """Launches a command in a new terminal window."""
        try:
            if self.os_type == 'Linux':
                # Try gnome-terminal first, then x-terminal-emulator
                # We wrap the command in bash to keep the window open
                full_cmd = f"echo '{title}'; echo '===================='; {command}; echo ''; read -p 'Press Enter to close...' var"
                
                try:
                    subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', full_cmd])
                except FileNotFoundError:
                    # Fallback
                    subprocess.Popen(['x-terminal-emulator', '-e', f"bash -c \"{full_cmd}\""])
                    
            elif self.os_type == 'Windows':
                # start cmd /k keeps window open
                subprocess.Popen(['start', 'cmd', '/k', f"echo {title} & echo ==================== & {command}"], shell=True)
                
            elif self.os_type == 'Darwin': # MacOS
                # AppleScript to open Terminal
                script = f'''tell application "Terminal" to do script "{command}"'''
                subprocess.Popen(['osascript', '-e', script])
                
        except Exception as e:
            print(f"Failed to open terminal: {e}")
            self.speaker.speak("I could not open a new terminal window.")

    def _get_ip_address(self):
        self.speaker.speak("Checking IP address.", blocking=False)
        if self.os_type == 'Windows':
            self._run_in_separate_terminal('ipconfig', "IP ADDRESS")
        else:
            self._run_in_separate_terminal('hostname -I', "IP ADDRESS")

    def _check_memory(self):
        self.speaker.speak("Checking memory usage.", blocking=False)
        if self.os_type == 'Linux':
            self._run_in_separate_terminal('free -h', "MEMORY USAGE")
        elif self.os_type == 'Darwin':
            self._run_in_separate_terminal('vm_stat', "MEMORY USAGE")
        elif self.os_type == 'Windows':
            self._run_in_separate_terminal('systeminfo', "MEMORY USAGE")

    def _check_disk(self):
        self.speaker.speak("Checking disk storage.", blocking=False)
        if self.os_type == 'Windows':
             self._run_in_separate_terminal('wmic logicaldisk get size,freespace,caption', "DISK STORAGE")
        else:
             self._run_in_separate_terminal('df -h .', "DISK STORAGE")

    def _list_files(self):
        self.speaker.speak("Listing files in current directory.", blocking=False)
        if self.os_type == 'Windows':
            self._run_in_separate_terminal('dir', "CURRENT DIRECTORY")
        else:
            self._run_in_separate_terminal('ls -la', "CURRENT DIRECTORY")

    def _run_security_scan(self):
        self.speaker.speak("Initiating system security scan.", blocking=False)
        
        if self.os_type == 'Linux':
             # Prefer rkhunter, then clamav, auto-install rkhunter if neither
             if os.system("which rkhunter > /dev/null 2>&1") == 0:
                self._run_in_separate_terminal('sudo rkhunter --check --sk', "SECURITY SCAN")
             elif os.system("which clamscan > /dev/null 2>&1") == 0:
                self._run_in_separate_terminal('clamscan -r ~', "SECURITY SCAN (ClamAV)")
             else:
                # If neither, try to install rkhunter
                cmd = self._get_cmd_with_auto_install('rkhunter', 'rkhunter')
                # Need sudo for rkhunter check 
                if 'sudo apt install' in cmd:
                     # Helper returns raw command name at end, we need flags
                     # This is a bit complex for the helper, so we construct manually for this complex case
                     cmd = "echo 'Installing rkhunter...'; sudo apt install rkhunter -y; sudo rkhunter --propupd; sudo rkhunter --check --sk"
                     self._run_in_separate_terminal(cmd, "SECURITY SCAN (Installing...)")
                else: 
                     # Should not happen given logic above, but fallback
                     self._run_in_separate_terminal('sudo rkhunter --check --sk', "SECURITY SCAN")
                
        elif self.os_type == 'Windows':
            # Windows Defender Scan (using PowerShell for reliability)
            # MpCmdRun.exe path can vary, but Start-MpScan is standard on Win10/11
            ps_cmd = "Start-MpScan -ScanType QuickScan"
            self._run_in_separate_terminal(f"powershell -Command \"{ps_cmd}\"", "WINDOWS DEFENDER SCAN")
            
        elif self.os_type == 'Darwin': # MacOS
            # Check Gatekeeper and SIP status
            mac_cmd = 'echo "Gatekeeper Status:"; spctl --status; echo ""; echo "System Integrity Protection:"; csrutil status'
            self._run_in_separate_terminal(mac_cmd, "SECURITY STATUS")

    def _check_ports(self):
        self.speaker.speak("Checking open network ports.", blocking=False)
        if self.os_type == 'Linux':
            self._run_in_separate_terminal('sudo ss -tulnp', "OPEN PORTS")
        else:
             self._run_in_separate_terminal('netstat -an', "OPEN PORTS")

    def _check_firewall(self):
        self.speaker.speak("Checking firewall status.", blocking=False)
        if self.os_type == 'Linux':
            self._run_in_separate_terminal('sudo ufw status verbose', "FIREWALL STATUS")
        elif self.os_type == 'Windows':
             self._run_in_separate_terminal('netsh advfirewall show allprofiles', "FIREWALL STATUS")

    def _check_connections(self):
        self.speaker.speak("Listing active network connections.", blocking=False)
        if self.os_type == 'Linux':
             self._run_in_separate_terminal('sudo ss -putan', "NETWORK CONNECTIONS")
        elif self.os_type == 'Windows':
             self._run_in_separate_terminal('netstat -ano', "NETWORK CONNECTIONS")
        elif self.os_type == 'Darwin':
             self._run_in_separate_terminal('netstat -an', "NETWORK CONNECTIONS")

    def _check_processes(self):
         self.speaker.speak("Opening process monitor.", blocking=False)
         if self.os_type == 'Linux':
             # Auto-install htop
             cmd = self._get_cmd_with_auto_install('htop', 'htop')
             self._run_in_separate_terminal(cmd, "PROCESS MONITOR")
         elif self.os_type == 'Windows':
              self._run_in_separate_terminal('tasklist', "PROCESS MONITOR")
         elif self.os_type == 'Darwin':
              self._run_in_separate_terminal('top', "PROCESS MONITOR")

    def _check_login_history(self):
         self.speaker.speak("Checking login history.", blocking=False)
         if self.os_type == 'Linux' or self.os_type == 'Darwin':
              self._run_in_separate_terminal('last', "LOGIN HISTORY")
         elif self.os_type == 'Windows':
              self._run_in_separate_terminal('query user', "LOGIN HISTORY")

    def _check_network_traffic(self):
         self.speaker.speak("Checking network traffic usage.", blocking=False)
         if self.os_type == 'Linux':
             # Try iftop first (needs sudo), then nload, then fallback
             if os.system("which iftop > /dev/null 2>&1") == 0:
                  self._run_in_separate_terminal('sudo iftop', "NETWORK TRAFFIC")
             elif os.system("which nload > /dev/null 2>&1") == 0:
                  self._run_in_separate_terminal('nload', "NETWORK TRAFFIC")
             else:
                  # Auto install iftop
                  cmd = "echo 'Installing iftop...'; sudo apt install iftop -y; sudo iftop"
                  self._run_in_separate_terminal(cmd, "NETWORK TRAFFIC (Installing...)")
                  
         elif self.os_type == 'Windows':
              self._run_in_separate_terminal('netstat -e', "NETWORK TRAFFIC (Bytes)")
         elif self.os_type == 'Darwin':
              self._run_in_separate_terminal('netstat -ib', "NETWORK TRAFFIC (Stats)")

    def _check_internet_speed(self):
        self.speaker.speak("Running internet speed test.", blocking=False)
        if self.os_type == 'Linux':
            # Fix 403 Error: Download latest script directly from GitHub
            # This bypasses the broken apt/pip versions entirely.
            cmd = (
                "echo 'Downloading latest speedtest-cli...'; "
                "curl -L https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -o /tmp/speedtest.py "
                "|| wget https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -O /tmp/speedtest.py; "
                "echo 'Running Speedtest...'; "
                "python3 /tmp/speedtest.py --secure"
            )
            self._run_in_separate_terminal(cmd, "SPEED TEST")
        elif self.os_type == 'Darwin':
             # Brew install speedtest-cli? Or just networkQuality (native)
             self._run_in_separate_terminal('networkQuality', "SPEED TEST")
        elif self.os_type == 'Windows':
             # Invoke-WebRequest usually not great for visuals, maybe just ping?
             # Or try to run fast.com in browser?
             # Let's try simple ping for now or check if speedtest cli exists
             self._run_in_separate_terminal('ping 8.8.8.8 -t', "PING TEST (Latency)")

    def _clean_system(self):
        self.speaker.speak("Starting system cleanup.", blocking=False)
        
        if self.os_type == 'Linux':
             # Safe cleanup: apt clean, autoremove (unused deps), and user thumbnail cache
             # Adding -y for non-interactive
             cmd = (
                 "echo 'Cleaning package cache...'; sudo apt-get clean; "
                 "echo 'Removing unused dependencies...'; sudo apt-get autoremove -y; "
                 "echo 'Clearing thumbnail cache...'; rm -rf ~/.cache/thumbnails/*; "
                 "echo 'Cleanup Complete!'"
             )
             self._run_in_separate_terminal(cmd, "SYSTEM CLEANUP")
             
        elif self.os_type == 'Windows':
             # Clean %TEMP% folder safely
             # Removed 'msg' command as it's not available on all editions (e.g. Home)
             # /q = quiet, /f = force, /s = subdirectories
             cmd = 'echo Cleaning temporary files... & del /q /f /s %TEMP%\\* & echo. & echo Cleanup Complete!'
             self._run_in_separate_terminal(cmd, "SYSTEM CLEANUP")
             
        elif self.os_type == 'Darwin': # MacOS
             # Clear User Caches and brew cleanup if available
             cmd = (
                 "echo 'Cleaning User Caches...'; rm -rf ~/Library/Caches/*; "
                 "if command -v brew &> /dev/null; then echo 'Running Homebrew Cleanup...'; brew cleanup; fi; "
                 "echo 'Cleanup Complete!'"
             )
             self._run_in_separate_terminal(cmd, "SYSTEM CLEANUP")



    def _kill_process(self, command):
        """Identifies and kills a running process based on user command with confirmation."""
        # Clean the command to get the app name
        ignore_words = ["kill", "close", "terminate", "stop", "running", "program", "application", "process", "task", "the", "please", "cortex"]
        
        words = command.lower().split()
        app_name = " ".join([w for w in words if w not in ignore_words]).strip()
        
        if not app_name:
            self.speaker.speak("Which application would you like me to close?")
            return

        self.speaker.speak(f"Are you sure you want to close {app_name}?")
        
        if self.listener:
            print("[Debug] Listening for confirmation...")
            confirmation = self.listener.listen()
            print(f"[Debug] Heard confirmation: '{confirmation}'")
            
            # Loose matching for confirmation
            if not confirmation:
                self.speaker.speak("Cancelled.")
                return
                
            conf_lower = confirmation.lower()
            valid_confirms = ["yes", "yeah", "yep", "sure", "do it", "go ahead", "confirm"]
            
            if not any(x in conf_lower for x in valid_confirms):
                 self.speaker.speak("Cancelled.")
                 return
        
        # Use key-value mapping and robust close logic
        close_application(app_name, self.speaker)
