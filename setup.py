#!/usr/bin/env python3
"""
Sunday Voice Assistant - Cross-Platform Setup Script
Automatically detects operating system and installs appropriate dependencies.
"""

import os
import sys
import platform
import subprocess
import venv
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")

def detect_os():
    """Detect the operating system"""
    os_type = platform.system()
    print_info(f"Detected OS: {os_type}")
    return os_type

def get_requirements_file(os_type):
    """Get the appropriate requirements file for the OS"""
    requirements_map = {
        'Linux': 'requirements-linux.txt',
        'Windows': 'requirements-windows.txt',
        'Darwin': 'requirements-macos.txt'
    }
    return requirements_map.get(os_type, 'requirements.txt')

def create_virtual_environment():
    """Create a virtual environment"""
    print_info("Creating virtual environment...")
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_warning("Virtual environment already exists. Skipping creation.")
        return True
    
    try:
        venv.create("venv", with_pip=True)
        print_success("Virtual environment created successfully")
        return True
    except Exception as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False

def get_python_executable():
    """Get the path to the Python executable in the virtual environment"""
    os_type = platform.system()
    if os_type == 'Windows':
        return Path("venv") / "Scripts" / "python.exe"
    else:
        return Path("venv") / "bin" / "python"

def get_pip_executable():
    """Get the path to the pip executable in the virtual environment"""
    os_type = platform.system()
    if os_type == 'Windows':
        return Path("venv") / "Scripts" / "pip.exe"
    else:
        return Path("venv") / "bin" / "pip"

def upgrade_pip():
    """Upgrade pip to the latest version"""
    print_info("Upgrading pip...")
    pip_exe = get_pip_executable()
    
    try:
        subprocess.run(
            [str(pip_exe), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        print_success("pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_warning(f"Failed to upgrade pip: {e}")
        return False

def install_requirements(requirements_file):
    """Install Python dependencies from requirements file"""
    print_info(f"Installing dependencies from {requirements_file}...")
    pip_exe = get_pip_executable()
    
    if not Path(requirements_file).exists():
        print_error(f"Requirements file not found: {requirements_file}")
        return False
    
    try:
        subprocess.run(
            [str(pip_exe), "install", "-r", requirements_file],
            check=True
        )
        print_success("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

def download_whisper_model():
    """Pre-download the Whisper model to avoid first-run delays"""
    print_info("Downloading Whisper model (this may take a minute)...")
    python_exe = get_python_executable()
    
    try:
        result = subprocess.run(
            [str(python_exe), "-c", 
             "from faster_whisper import WhisperModel; WhisperModel('base.en', device='cpu', compute_type='int8')"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            print_success("Whisper model downloaded successfully")
            return True
        else:
            print_warning("Whisper model download may have failed. It will download on first run.")
            return False
    except subprocess.TimeoutExpired:
        print_warning("Whisper model download timed out. It will download on first run.")
        return False
    except Exception as e:
        print_warning(f"Could not pre-download Whisper model: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible (3.9+)"""
    print_info("Checking Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print_error(f"Python 3.9+ required, but found {version.major}.{version.minor}")
        print_info("Please install Python 3.9 or later and try again")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def create_default_config_files():
    """Create default configuration files if they don't exist"""
    print_info("Creating default configuration files...")
    import json
    
    # Create user_config.json
    user_config_path = Path("data/user_config.json")
    if not user_config_path.exists():
        default_config = {
            "voice_rate": 175,
            "voice_volume": 1.0,
            "wake_word_enabled": False,
            "theme": "dark",
            "log_level": "INFO"
        }
        user_config_path.write_text(json.dumps(default_config, indent=2))
        print_success("Created data/user_config.json")
    
    # Create workspaces.json
    workspaces_path = Path("data/workspaces.json")
    if not workspaces_path.exists():
        os_type = platform.system()
        if os_type == "Windows":
            default_workspaces = {
                "home": str(Path.home()),
                "documents": str(Path.home() / "Documents"),
                "downloads": str(Path.home() / "Downloads"),
                "desktop": str(Path.home() / "Desktop")
            }
        else:
            default_workspaces = {
                "home": str(Path.home()),
                "documents": str(Path.home() / "Documents"),
                "downloads": str(Path.home() / "Downloads"),
                "desktop": str(Path.home() / "Desktop")
            }
        workspaces_path.write_text(json.dumps(default_workspaces, indent=2))
        print_success("Created data/workspaces.json")
    
    print_success("Configuration files ready")
    return True

def verify_installation():
    """Verify that installation completed successfully"""
    print_header("Verifying Installation")
    python_exe = get_python_executable()
    all_passed = True
    
    # Test 1: PyAudio import
    print_info("Testing PyAudio import...")
    try:
        result = subprocess.run(
            [str(python_exe), "-c", "import pyaudio; print('OK')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and "OK" in result.stdout:
            print_success("PyAudio available")
        else:
            print_warning("PyAudio may not be properly installed")
            all_passed = False
    except Exception as e:
        print_warning(f"Could not verify PyAudio: {e}")
        all_passed = False
    
    # Test 2: Whisper import
    print_info("Testing Whisper import...")
    try:
        result = subprocess.run(
            [str(python_exe), "-c", "from faster_whisper import WhisperModel; print('OK')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and "OK" in result.stdout:
            print_success("Whisper available")
        else:
            print_warning("Whisper may not be properly installed")
            all_passed = False
    except Exception as e:
        print_warning(f"Could not verify Whisper: {e}")
        all_passed = False
    
    # Test 3: Config files
    print_info("Checking configuration files...")
    if Path("data/user_config.json").exists() and Path("data/workspaces.json").exists():
        print_success("Configuration files present")
    else:
        print_warning("Some configuration files missing")
        all_passed = False
    
    if all_passed:
        print_success("All verification tests passed!")
    else:
        print_warning("Some verification tests failed, but you can still try running Sunday")
    
    return all_passed


def create_data_directories():
    """Create necessary data directories"""
    print_info("Creating data directories...")
    
    directories = [
        "data",
        "data/logs",
        "data/cache"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print_success("Data directories created")
    return True

def print_platform_specific_instructions(os_type):
    """Print platform-specific setup instructions"""
    print_header("Platform-Specific Setup")
    
    if os_type == 'Linux':
        print("For enhanced file manager integration, install optional tools:")
        print("  sudo apt install xdotool xclip    # Debian/Ubuntu")
        print("  sudo dnf install xdotool xclip    # Fedora")
        print("  sudo pacman -S xdotool xclip      # Arch Linux")
        print("\nFor Piper TTS (optional, higher quality):")
        print("  The piper engine is already included in piper_engine/")
        print("  Make sure piper_engine/piper/piper is executable:")
        print("  chmod +x piper_engine/piper/piper")
        
    elif os_type == 'Windows':
        print("Windows setup is complete!")
        print("\nOptional: For Piper TTS (higher quality), ensure:")
        print("  piper_engine/piper_windows/piper/piper.exe exists")
        print("\nNote: File selection works with Windows Explorer automatically.")
        
    elif os_type == 'Darwin':
        print("macOS setup is almost complete!")
        print("\nGrant permissions when prompted:")
        print("  - Microphone access (required for voice input)")
        print("  - Accessibility (may be required for some features)")
        print("\nNote: File selection uses clipboard method on macOS.")

def print_next_steps(os_type):
    """Print next steps for the user"""
    print_header("Setup Complete! 🎉")
    
    print("To start Sunday Voice Assistant:\n")
    
    if os_type == 'Windows':
        print("1. Activate the virtual environment:")
        print("   venv\\Scripts\\activate\n")
        print("2. Run the assistant:")
        print("   python main.py\n")
        print("Or use the provided batch file:")
        print("   start.bat\n")
    else:
        print("1. Activate the virtual environment:")
        print("   source venv/bin/activate\n")
        print("2. Run the assistant:")
        print("   python main.py\n")
    
    print("For more information, see:")
    print("  - README.md (general information)")
    print("  - INSTALL.md (detailed installation guide)")
    print(f"  - docs/{os_type.lower()}-setup.md (platform-specific setup)")

def main():
    """Main setup function"""
    print_header("Sunday Voice Assistant - Setup")
    
    # Check Python version first
    if not check_python_version():
        return 1
    
    # Detect OS
    os_type = detect_os()
    requirements_file = get_requirements_file(os_type)
    
    # Create virtual environment
    if not create_virtual_environment():
        print_error("Setup failed: Could not create virtual environment")
        return 1
    
    # Upgrade pip
    upgrade_pip()
    
    # Install requirements
    if not install_requirements(requirements_file):
        print_error("Setup failed: Could not install dependencies")
        return 1
    
    # Create data directories
    create_data_directories()
    
    # Create default config files
    create_default_config_files()
    
    # Download Whisper model (optional, best effort)
    download_whisper_model()
    
    # Verify installation
    verify_installation()
    
    # Print platform-specific instructions
    print_platform_specific_instructions(os_type)
    
    # Print next steps
    print_next_steps(os_type)
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
