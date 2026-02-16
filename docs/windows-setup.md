# Windows Setup Guide - Sunday Voice Assistant

This guide covers Windows-specific setup, configuration, and troubleshooting for Sunday.

## System Requirements

- **OS**: Windows 10 or Windows 11
- **Python**: 3.9+ (3.10 or 3.11 recommended)
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk**: ~2GB for models and dependencies

## Prerequisites

### 1. Install Python

Download Python from [python.org](https://www.python.org/downloads/):

⚠️ **IMPORTANT**: During installation:
- ✅ Check "Add Python to PATH"
- ✅ Check "Install for all users" (optional)
- Choose "Customize installation" to enable all features

Verify installation:
```cmd
python --version
```

### 2. Install Visual C++ Build Tools

Some Python packages require compilation. Download and install:
[Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

Or install Visual Studio Community with "Desktop development with C++" workload.

### 3. Install Git (Optional)

Download from [git-scm.com](https://git-scm.com/download/win)

Or use GitHub Desktop if you prefer a GUI.

## Installation

### Method 1: Automated Setup (Recommended)

1. **Download the project**
   
   Using Git:
   ```cmd
   git clone https://github.com/Thanga-Prasath/Sunday-final-year.git
   cd Sunday-final-year
   ```
   
   Or download ZIP from GitHub and extract it.

2. **Run the setup script**
   ```cmd
   python setup.py
   ```
   
   This will:
   - Create a virtual environment
   - Install Windows-specific dependencies
   - Download AI models (~140MB)
   - Configure the application

3. **Run Sunday**
   
   Double-click `start.bat` or:
   ```cmd
   venv\Scripts\activate
   python main.py
   ```

### Method 2: Manual Setup

If automatic setup fails:

```cmd
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install PyAudio (special handling for Windows)
pip install pipwin
pipwin install pyaudio

# Install other dependencies
pip install -r requirements-windows.txt

# Download Whisper model
python -c "from faster_whisper import WhisperModel; WhisperModel('base.en')"

# Run Sunday
python main.py
```

## Permissions Setup

### Microphone Access

1. Go to **Settings** → **Privacy** → **Microphone**
2. Enable "Allow apps to access your microphone"
3. Enable access for Python

### Windows Defender / Firewall

If Windows Defender blocks the application:

1. Allow Python through the firewall when prompted
2. Or manually: **Windows Security** → **Firewall & network protection** → **Allow an app through firewall**
3. Add Python to the allowed list

## Piper TTS Setup (Optional)

Piper provides higher quality text-to-speech on Windows.

### Enable Piper

The Piper binary is included in `piper_engine\piper_windows\piper\piper.exe`.

Sunday will automatically use it if available.

### Verify Piper

Test from PowerShell:
```powershell
echo "Hello from Piper" | .\piper_engine\piper_windows\piper\piper.exe --model .\piper_engine\voice.onnx --output_file test.wav

# Play the file
.\test.wav
```

### Alternative Voice Models

Download voices from [Piper Releases](https://github.com/rhasspy/piper/releases):

1. Download a `.onnx` voice model
2. Replace `piper_engine\voice.onnx`
3. Restart Sunday

## File Selection Integration

Sunday integrates with Windows Explorer automatically using PowerShell COM objects.

### How It Works

1. Select files in Windows Explorer
2. Say "Move selected files to Documents"
3. Sunday reads the selection and performs the action

No additional setup needed!

### Troubleshooting File Selection

If file selection doesn't work:

**Check PowerShell execution policy:**
```powershell
Get-ExecutionPolicy
```

If it's "Restricted", change it:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Common Issues

### PyAudio Installation Fails

**Error:**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solution 1: Use pipwin (easiest)**
```cmd
pip install pipwin
pipwin install pyaudio
```

**Solution 2: Install manually**
Download PyAudio wheel from [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio):

```cmd
# Example for Python 3.11, 64-bit
pip install PyAudio‑0.2.13‑cp311‑cp311‑win_amd64.whl
```

### "Python not found" Error

Python not in PATH. Reinstall Python and check "Add Python to PATH".

Or add manually:
1. Find Python installation (usually `C:\Users\<user>\AppData\Local\Programs\Python\Python311`)
2. Add to PATH: **System** → **Environment Variables** → Edit PATH → Add Python directory

### Microphone Not Working

1. **Check Windows Settings**
   - Settings → Privacy → Microphone
   - Enable for desktop apps

2. **Test Microphone**
   - Settings → System → Sound → Input → Test your microphone

3. **Select Correct Device**
   - Right-click speaker icon → Sounds → Recording
   - Set correct microphone as default

### Antivirus Blocking

Some antivirus software may block Python or downloaded models:

1. Add Python installation folder to exceptions
2. Add Sunday project folder to exceptions
3. Temporarily disable antivirus during installation

### "ImportError: DLL load failed"

Install Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

### UI Window Doesn't Show

```cmd
# Reinstall PyQt6
pip install --force-reinstall PyQt6
```

## Performance Optimization

### Use Faster Whisper Model

Edit `core\listening.py`:
```python
self.model_size = "tiny.en"  # Faster, less accurate
```

### Use GPU (NVIDIA Only)

If you have an NVIDIA GPU:

```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

Edit `core\listening.py`:
```python
device = "cuda"
compute_type = "float16"
```

### Adjust Voice Speed

Edit `data\user_config.json`:
```json
{
  "voice_rate": 175,
  "voice_volume": 1.0
}
```

## Startup on Windows Boot

### Method 1: Task Scheduler

1. Open **Task Scheduler**
2. Create Basic Task → Name it "Sunday Assistant"
3. Trigger: When I log on
4. Action: Start a program
5. Program: `C:\path\to\Sunday-final-year\start.bat`

### Method 2: Startup Folder

Create a shortcut:
1. Right-click `start.bat` → Create shortcut
2. Press `Win+R`, type `shell:startup`
3. Move the shortcut to the Startup folder

## Uninstallation

```cmd
cd Sunday-final-year

# Deactivate virtual environment if active
deactivate

# Delete the project folder
cd ..
rmdir /s Sunday-final-year
```

## Windows-Specific Commands

Sunday supports Windows-specific features:

| Say This | Action |
|----------|--------|
| "Open Control Panel" | Opens Control Panel |
| "Empty Recycle Bin" | Empties the bin |
| "Lock computer" | Locks Windows |
| "Sleep computer" | Puts PC to sleep |
| "Show hidden files" | Toggles hidden files in Explorer |
| "Minimize all windows" | Windows+D |

## Compatibility Notes

### Windows 10 vs 11

Both are fully supported. Windows 11 has better microphone privacy controls.

### 32-bit vs 64-bit

Only 64-bit Windows is supported. Python 64-bit is recommended for all AI models.

### Windows on ARM

Not tested but should work with Python ARM64 builds.

## Troubleshooting PowerShell Scripts

If PowerShell scripts fail:

```powershell
# Check execution policy
Get-ExecutionPolicy

# Set to allow local scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or bypass for single session
powershell -ExecutionPolicy Bypass -File script.ps1
```

## Getting Help

1. Check `data\logs\` for error messages
2. Run from Command Prompt to see errors:
   ```cmd
   venv\Scripts\activate
   python main.py
   ```
3. File an issue on GitHub with:
   - Windows version (Settings → System → About)
   - Python version
   - Error messages
   - Screenshot if UI issue

## Advanced Configuration

### Custom Install Location

Install to a different drive:

```cmd
# Example: Install to D:\Sunday
git clone https://github.com/Thanga-Prasath/Sunday-final-year.git D:\Sunday
cd D:\Sunday
python setup.py
```

### Network Drive Storage

You can store models on a network drive to save local space:

```cmd
# Create junction
mklink /J piper_engine Z:\shared\sunday\piper_engine
```

---

**Next Steps:**
- Configure workspaces in `data\workspaces.json`
- Customize voice speed in `data\user_config.json`
- Read [README.md](../README.md) for usage examples
