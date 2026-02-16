"""
Dependency Management Utility for Sunday Voice Assistant

Provides functions to check for and install system dependencies
automatically based on the operating system.
"""

import subprocess
import platform
import shutil
import os
from typing import List, Optional

class DependencyManager:
    """Manages system-level dependencies for Sunday components"""
    
    def __init__(self):
        self.os_type = platform.system()
        self._installed_cache = {}
    
    def is_command_available(self, command: str) -> bool:
        """
        Check if a system command is available.
        
        Args:
            command: Command name to check (e.g. 'xdotool')
            
        Returns:
            True if command is available, False otherwise
        """
        # Check cache first
        if command in self._installed_cache:
            return self._installed_cache[command]
        
        # Check using shutil.which
        result = shutil.which(command) is not None
        self._installed_cache[command] = result
        return result
    
    def install_linux_package(self, package_name: str, command_name: str = None, silent: bool = False) -> bool:
        """
        Install a package on Linux using the appropriate package manager.
        Opens in a separate terminal window for user visibility.
        
        Args:
            package_name: Name of the package to install
            command_name: Name of the command to verify (if different from package_name)
            silent: If True, suppress output (not recommended for interactive installs)
            
        Returns:
            True if installed successfully, False otherwise
        """
        if self.os_type != 'Linux':
            return False
        
        # Use command_name for verification if provided, otherwise use package_name
        verify_command = command_name if command_name else package_name
        
        # Detect package manager and build command
        if shutil.which('apt-get'):
            cmd = f'sudo apt-get install -y {package_name}'
            title = f"Installing {package_name} (apt)"
        elif shutil.which('dnf'):
            cmd = f'sudo dnf install -y {package_name}'
            title = f"Installing {package_name} (dnf)"
        elif shutil.which('yum'):
            cmd = f'sudo yum install -y {package_name}'
            title = f"Installing {package_name} (yum)"
        elif shutil.which('pacman'):
            cmd = f'sudo pacman -S --noconfirm {package_name}'
            title = f"Installing {package_name} (pacman)"
        else:
            print(f"[Dependency] No supported package manager found for {package_name}")
            return False
        
        try:
            print(f"[Dependency] Opening terminal to install {package_name}...")
            print(f"[Dependency] Please enter your password when prompted")
            
            # Open in a separate terminal window for user visibility
            # Try different terminal emulators
            terminal_commands = [
                f"x-terminal-emulator -e 'bash -c \"{cmd}; echo; echo Installation complete. Press Enter to close...; read\"'",
                f"gnome-terminal -- bash -c '{cmd}; echo; echo \"Installation complete. Press Enter to close...\"; read'",
                f"konsole -e bash -c '{cmd}; echo; echo \"Installation complete. Press Enter to close...\"; read'",
                f"xfce4-terminal -e 'bash -c \"{cmd}; echo; echo Installation complete. Press Enter to close...; read\"'",
                f"xterm -e 'bash -c \"{cmd}; echo; echo Installation complete. Press Enter to close...; read\"'",
            ]
            
            terminal_opened = False
            for terminal_cmd in terminal_commands:
                try:
                    # Try to open the terminal
                    subprocess.Popen(terminal_cmd, shell=True)
                    terminal_opened = True
                    print(f"[Dependency] Terminal opened for installation")
                    break
                except Exception:
                    continue
            
            if not terminal_opened:
                # Fallback: run in current terminal if no GUI terminal found
                print(f"[Dependency] No GUI terminal found, installing in current terminal...")
                result = subprocess.run(
                    cmd,
                    shell=True,
                    timeout=300
                )
                if result.returncode == 0:
                    print(f"[Dependency] ✅ {package_name} installed successfully")
                    self._installed_cache[verify_command] = True
                    return True
                else:
                    print(f"[Dependency] ❌ Failed to install {package_name}")
                    return False
            
            # Wait a moment for installation to start
            import time
            time.sleep(2)
            
            # Give user time to complete installation
            print(f"[Dependency] Waiting for installation to complete...")
            # Wait up to 5 minutes, checking every 5 seconds
            for i in range(60):  # 60 * 5 seconds = 5 minutes
                time.sleep(5)
                # Check if the actual command is now available
                if self.is_command_available(verify_command):
                    print(f"[Dependency] ✅ {package_name} installed successfully")
                    return True
            
            # If we got here, either installation is taking too long or failed
            # Check one more time
            if self.is_command_available(verify_command):
                print(f"[Dependency] ✅ {package_name} installed successfully")
                return True
            else:
                print(f"[Dependency] ⚠️  Installation may have failed or is still in progress")
                print(f"[Dependency] Please verify manually: which {verify_command}")
                return False
            
        except Exception as e:
            print(f"[Dependency] ❌ Error installing {package_name}: {e}")
            return False
    
    def ensure_dependencies(self, dependencies: List[str], auto_install: bool = True) -> bool:
        """
        Ensure all dependencies are available, optionally installing missing ones.
        Opens terminal windows on all platforms for user visibility.
        
        Args:
            dependencies: List of command names to check
            auto_install: If True, attempt to install missing dependencies
            
        Returns:
            True if all dependencies are available, False otherwise
        """
        all_available = True
        missing = []
        
        for dep in dependencies:
            if not self.is_command_available(dep):
                missing.append(dep)
                all_available = False
        
        if not missing:
            return True
        
        if not auto_install:
            print(f"[Dependency] Missing dependencies: {', '.join(missing)}")
            return False
        
        # Install missing dependencies based on platform
        if self.os_type == 'Linux':
            for dep in missing:
                self.install_linux_package(dep)
            
            # Re-check after installation
            all_available = all(self.is_command_available(dep) for dep in dependencies)
            
        elif self.os_type == 'Darwin':  # macOS
            print(f"[Dependency] Installing on macOS using Homebrew...")
            for dep in missing:
                self.install_macos_package(dep)
            
            # Re-check after installation
            all_available = all(self.is_command_available(dep) for dep in dependencies)
            
        elif self.os_type == 'Windows':
            print(f"[Dependency] Windows requires manual installation for some packages")
            for dep in missing:
                self.install_windows_package(dep)
            
            # Windows packages typically need manual installation
            all_available = False
        else:
            print(f"[Dependency] Auto-install not supported on {self.os_type}")
            print(f"[Dependency] Please manually install: {', '.join(missing)}")
            all_available = False
        
        return all_available
    
    def install_macos_package(self, package_name: str) -> bool:
        """
        Install a package on macOS using Homebrew.
        Opens Terminal.app with installation command.
        
        Args:
            package_name: Name of the package to install
            
        Returns:
            True if installed successfully, False otherwise
        """
        if self.os_type != 'Darwin':
            return False
        
        # Check if Homebrew is available
        if not shutil.which('brew'):
            print("[Dependency] Homebrew is not installed!")
            print("[Dependency] Install from: https://brew.sh")
            # Open browser to Homebrew website
            try:
                subprocess.run(['open', 'https://brew.sh'])
            except:
                pass
            return False
        
        try:
            print(f"[Dependency] Opening Terminal to install {package_name}...")
            print(f"[Dependency] Please enter your password when prompted")
            
            # Build the command
            cmd = f'brew install {package_name}'
            
            # Open Terminal.app with the command
            applescript = f'''
            tell application "Terminal"
                activate
                do script "{cmd}; echo ''; echo 'Installation complete. You can close this window.'"
            end tell
            '''
            
            subprocess.Popen(['osascript', '-e', applescript])
            print(f"[Dependency] Terminal opened for installation")
            
            # Wait for installation to complete
            import time
            time.sleep(2)
            
            print(f"[Dependency] Waiting for installation to complete...")
            for i in range(60):  # 5 minutes max
                time.sleep(5)
                if self.is_command_available(package_name):
                    print(f"[Dependency] ✅ {package_name} installed successfully")
                    return True
            
            # Final check
            if self.is_command_available(package_name):
                print(f"[Dependency] ✅ {package_name} installed successfully")
                return True
            else:
                print(f"[Dependency] ⚠️  Installation may have failed or is still in progress")
                return False
                
        except Exception as e:
            print(f"[Dependency] ❌ Error installing {package_name}: {e}")
            return False
    
    def install_windows_package(self, package_name: str) -> bool:
        """
        Show installation instructions for Windows in a visible window.
        Windows doesn't have a universal package manager, so we guide the user.
        
        Args:
            package_name: Name of the package to install
            
        Returns:
            False (manual installation required)
        """
        if self.os_type != 'Windows':
            return False
        
        try:
            print(f"[Dependency] Opening PowerShell with installation instructions for {package_name}...")
            
            # Create installation instructions based on package
            if package_name in ['xdotool', 'xclip']:
                instructions = f"# {package_name} is Linux-specific and not needed on Windows.\n# Windows has built-in alternatives.\n\nWrite-Host 'No action required - {package_name} not needed on Windows' -ForegroundColor Green\n\nWrite-Host '\nPress any key to close...'\n$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"
            elif package_name == 'clamav':
                instructions = f"Write-Host 'Installing {package_name} on Windows' -ForegroundColor Cyan\nWrite-Host ''\nWrite-Host 'ClamAV for Windows can be downloaded from:'\nWrite-Host 'https://www.clamav.net/downloads' -ForegroundColor Yellow\nWrite-Host ''\nWrite-Host 'Alternative: Windows Defender is built-in and recommended for Windows'\nWrite-Host ''\nWrite-Host 'Opening download page in browser...'\nStart-Process 'https://www.clamav.net/downloads'\nWrite-Host ''\nWrite-Host 'Press any key to close...'\n$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"
            else:
                instructions = f"Write-Host 'Package: {package_name}' -ForegroundColor Cyan\nWrite-Host ''\nWrite-Host 'This package needs to be installed manually on Windows.'\nWrite-Host 'Please search for \"{package_name} for Windows\" or consult the documentation.'\nWrite-Host ''\nWrite-Host 'Press any key to close...'\n$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"
            
            # Open PowerShell window with instructions
            cmd = f'powershell.exe -NoExit -Command "{instructions}"'
            subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE if self.os_type == 'Windows' else 0)
            
            print(f"[Dependency] PowerShell opened with installation instructions")
            print(f"[Dependency] Please follow the instructions in the PowerShell window")
            
            return False  # Manual installation required
            
        except Exception as e:
            print(f"[Dependency] ❌ Error showing instructions for {package_name}: {e}")
            return False
    
    def get_installation_instructions(self, package: str) -> Optional[str]:
        """
        Get manual installation instructions for a package.
        
        Args:
            package: Package name
            
        Returns:
            Installation command string or None
        """
        if self.os_type == 'Linux':
            if shutil.which('apt-get'):
                return f"sudo apt-get install -y {package}"
            elif shutil.which('dnf'):
                return f"sudo dnf install -y {package}"
            elif shutil.which('pacman'):
                return f"sudo pacman -S {package}"
        elif self.os_type == 'Windows':
            if package in ['xdotool', 'xclip']:
                return f"{package} is not available on Windows (not needed)"
            return f"Install {package} manually"
        elif self.os_type == 'Darwin':  # macOS
            return f"brew install {package}"
        
        return None

# Global instance for easy access
_dependency_manager = None

def get_dependency_manager() -> DependencyManager:
    """Get the global DependencyManager instance"""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager

# Convenience functions
def ensure_commands(commands: List[str], auto_install: bool = True) -> bool:
    """
    Ensure system commands are available.
    
    Args:
        commands: List of command names to check/install
        auto_install: Whether to auto-install if missing
        
    Returns:
        True if all commands are available
    """
    dm = get_dependency_manager()
    return dm.ensure_dependencies(commands, auto_install)

def is_available(command: str) -> bool:
    """Check if a command is available on the system"""
    dm = get_dependency_manager()
    return dm.is_command_available(command)

# Example usage
if __name__ == "__main__":
    dm = DependencyManager()
    
    # Check for xdotool and xclip
    print("Testing dependency management...")
    
    if dm.is_command_available('xdotool'):
        print("✅ xdotool is available")
    else:
        print("❌ xdotool is not available")
        if input("Install xdotool? (y/n): ").lower() == 'y':
            dm.install_linux_package('xdotool', silent=False)
    
    # Ensure multiple dependencies
    required = ['xdotool', 'xclip']
    if dm.ensure_dependencies(required, auto_install=False):
        print(f"✅ All dependencies available: {required}")
    else:
        print(f"❌ Some dependencies missing")
