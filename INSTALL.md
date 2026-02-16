# Sunday Voice Assistant - Installation Guide

This guide provides detailed installation instructions for all supported platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Windows](#windows)
  - [Linux](#linux)
  - [macOS](#macos)
- [First Run](#first-run)
- [Troubleshooting](#troubleshooting)
- [Advanced Setup](#advanced-setup)

## Prerequisites

### All Platforms

1. **Python 3.9+** (Python 3.10 or 3.11 recommended)
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to add Python to PATH during installation

2. **Git** (for cloning the repository)
   - Download from [git-scm.com](https://git-scm.com/downloads/)

3. **Microphone and Speakers/Headphones**

4. **Internet Connection** (for initial model downloads)

### Platform-Specific Prerequisites

#### Windows
- Windows 10 or higher
- Microsoft Visual C++ 14.0+ (for some Python packages)
  - Download from [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

#### Linux
- Any modern distribution (Ubuntu 20.04+, Fedora 35+, Arch, Manjaro, etc.)
- Development tools: `sudo apt install build-essential python3-dev portaudio19-dev`

#### macOS
- macOS 11 Big Sur or higher
- Xcode Command Line Tools: `xcode-select --install`

## Installation

### Windows

1. **Clone the repository**
   ```cmd
   git clone https://github.com/Thanga-Prasath/Sunday-final-year.git
   cd Sunday-final-year
   ```

2. **Run the setup script**
   ```cmd
   python setup.py
   ```
   
   This will:
   - Create a virtual environment
   - Install Windows-specific dependencies
   - Download AI models (~140MB)
   - Set up configuration files

3. **Activate the virtual environment**
   ```cmd
   venv\Scripts\activate
   ```

4. **Run Sunday**
   ```cmd
   python main.py
   ```
   
   Or simply double-click `start.bat`

**Grant Permissions:**
- Allow microphone access when prompted
- Allow network access for Windows Firewall if prompted

### Linux

1. **Install system dependencies**
   
   **Debian/Ubuntu:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv build-essential portaudio19-dev
   ```
   
   **Fedora:**
   ```bash
   sudo dnf install python3 python3-pip python3-devel portaudio-devel
   ```
   
   **Arch Linux:**
   ```bash
   sudo pacman -S python python-pip portaudio
   ```

2. **Clone the repository**
   ```bash
   git clone https://github.com/Thanga-Prasath/Sunday-final-year.git
   cd Sunday-final-year
   ```

3. **Run the setup script**
   ```bash
   python3 setup.py
   ```

4. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

5. **Run Sunday**
   ```bash
   python main.py
   ```

**Optional: Enhanced file manager integration**
```bash
# Debian/Ubuntu
sudo apt install xdotool xclip

# Fedora
sudo dnf install xdotool xclip

# Arch Linux
sudo pacman -S xdotool xclip
```

**Optional: Piper TTS (better voice quality)**
```bash
chmod +x piper_engine/piper/piper
```

### macOS

1. **Install Homebrew** (if not already installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install dependencies**
   ```bash
   brew install python@3.11 portaudio
   ```

3. **Clone the repository**
   ```bash
   git clone https://github.com/Thanga-Prasath/Sunday-final-year.git
   cd Sunday-final-year
   ```

4. **Run the setup script**
   ```bash
   python3 setup.py
   ```

5. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

6. **Run Sunday**
   ```bash
   python3 main.py
   ```

**Grant Permissions:**
- Go to System Preferences > Security & Privacy > Privacy
- Enable Microphone access for Terminal/Python
- Enable Accessibility access if prompted (for window management)

## First Run

### What to Expect

1. **Model Loading** - First run downloads the Whisper AI model (~140MB). This happens once.
   ```
   [System] Loading Whisper Model (base.en)...
   [System] This should take just a few seconds...
   ```

2. **Noise Calibration** - The system calibrates to your microphone
   ```
   Calibrating background noise... (Please stay quiet)
   Calibration Complete. Threshold set to: 450.12
   ```

3. **UI Launch** - The status window appears in the system tray

4. **Listening** - You'll see "Listening..." when ready for commands

### Testing Your Installation

Try these simple commands:
1. "What time is it?"
2. "Hello Sunday"
3. "System information"

If Sunday responds correctly, installation was successful! 🎉

## Troubleshooting

### Common Issues

#### "No module named 'pyaudio'"

**Windows:**
```cmd
pip install pipwin
pipwin install pyaudio
```

**Linux:**
```bash
sudo apt install portaudio19-dev
pip install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

#### "Microphone not detected"

**Windows:**
- Settings > Privacy > Microphone > Allow apps to access microphone
- Check device in Settings > System > Sound > Input

**Linux:**
```bash
# Test microphone
arecord -l
# Adjust volume
alsamixer
```

**macOS:**
- System Preferences > Security & Privacy > Microphone
- Ensure Terminal/Python has access

#### "Whisper model download failed"

```bash
# Manual download
python -c "from faster_whisper import WhisperModel; WhisperModel('base.en')"
```

#### "Import error: DLL load failed" (Windows)

Install Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

#### "Permission denied: piper" (Linux)

```bash
chmod +x piper_engine/piper/piper
```

#### Voice is too fast/slow

Edit `data/user_config.json`:
```json
{
  "voice_rate": 175,
  "voice_volume": 1.0
}
```
- Lower rate = slower speech (range: 50-300)
- Volume: 0.0-1.0

### Still Having Issues?

1. Check platform-specific guides:
   - [Linux Setup Guide](docs/linux-setup.md)
   - [Windows Setup Guide](docs/windows-setup.md)
   - [macOS Setup Guide](docs/macos-setup.md)

2. Verify Python version:
   ```bash
   python --version  # Should be 3.9+
   ```

3. Reinstall dependencies:
   ```bash
   pip install -r requirements-<your-os>.txt --force-reinstall
   ```

4. Check logs in `data/logs/` directory

## Advanced Setup

### Custom Wake Words

Currently, Sunday doesn't use wake words but activates on any speech. To modify this behavior, edit `core/listening.py`.

### Custom Voice Models

To use different Whisper models, edit `core/listening.py`:
```python
self.model_size = "small.en"  # Options: tiny.en, base.en, small.en, medium.en
```

### Piper TTS Setup

**Linux:**
Piper binaries are in `piper_engine/piper/`

**Windows:**
Piper binaries are in `piper_engine/piper_windows/piper/`

To change voice models, replace `piper_engine/voice.onnx` with another model from:
https://github.com/rhasspy/piper/releases

### Environment Variables

Create a `.env` file for advanced configuration:
```env
WHISPER_MODEL=base.en
LOG_LEVEL=INFO
USE_PIPER=true
```

## Performance Optimization

### Low-End Systems

Use a smaller Whisper model:
```python
# In core/listening.py
self.model_size = "tiny.en"  # Faster but less accurate
```

### High-End Systems

Use a larger model for better accuracy:
```python
self.model_size = "small.en"  # More accurate but slower
```

### GPU Acceleration (Advanced)

If you have an NVIDIA GPU:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

Then edit `core/listening.py`:
```python
device = "cuda"  # Instead of "cpu"
compute_type = "float16"  # Instead of "int8"
```

---

**Next Steps:**
- See [README.md](README.md) for usage examples
- Configure workspaces in `data/workspaces.json`
- Customize app names in `data/apps.json`
