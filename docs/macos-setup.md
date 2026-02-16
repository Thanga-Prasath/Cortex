# macOS Setup Guide - Sunday Voice Assistant

This guide covers macOS-specific setup, configuration, and troubleshooting for Sunday.

## System Requirements

- **OS**: macOS 11 Big Sur or later
- **Python**: 3.9+ (3.10 or 3.11 recommended)
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk**: ~2GB for models and dependencies

## Prerequisites

### 1. Install Homebrew

Homebrew is the package manager for macOS. Install it if you haven't:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen instructions to add Homebrew to your PATH.

### 2. Install Python

```bash
brew install python@3.11
```

Verify installation:
```bash
python3 --version
```

### 3. Install Xcode Command Line Tools

Required for compiling some Python packages:

```bash
xcode-select --install
```

### 4. Install System Dependencies

```bash
brew install portaudio git
```

## Installation

### Quick Install

1. **Clone the repository**
   ```bash
   git clone https://github.com/Thanga-Prasath/Sunday-final-year.git
   cd Sunday-final-year
   ```

2. **Run setup**
   ```bash
   python3 setup.py
   ```

3. **Activate virtual environment**
   ```bash
   source venv/bin/activate
   ```

4. **Run Sunday**
   ```bash
   python main.py
   ```

### Manual Installation

If automatic setup fails:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements-macos.txt

# Download Whisper model
python -c "from faster_whisper import WhisperModel; WhisperModel('base.en')"

# Run Sunday
python main.py
```

## Permissions Setup

macOS requires explicit permissions for microphone and accessibility features.

### Microphone Permission

1. Go to **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Microphone** from the left sidebar
3. Add and enable **Terminal** (or your Python executor)
4. You may need to add **Python** itself if running directly

### Accessibility Permission (Optional)

For window management features:

1. Go to **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Accessibility**
3. Click the lock to make changes
4. Add **Terminal** and/or **Python**

## Text-to-Speech

macOS has excellent built-in TTS (via pyttsx3). No additional setup needed!

### Change Voice

Edit `core/speaking.py` to select different macOS voices:

```python
# Available voices: Samantha, Alex, Victoria, Karen, etc.
# Sunday auto-selects Samantha or Alex by default
```

List available voices:
```bash
say -v "?"
```

Test a voice:
```bash
say -v Samantha "Hello from Sunday"
```

## File Selection Integration

macOS file selection uses a basic clipboard method by default.

### How It Works

1. Select files in Finder
2. Press `Cmd+C` to copy
3. Say "Move selected files to Documents"

### Advanced: AppleScript Integration (Optional)

For better Finder integration, you can extend Sunday with AppleScript:

```applescript
tell application "Finder"
    set selectedFiles to selection as alias list
end tell
```

This would require modifying `components/file_manager/detection.py` to call AppleScript.

## Common Issues

### PyAudio Installation Fails

**Error:**
```
fatal error: 'portaudio.h' file not found
```

**Solution:**
```bash
brew install portaudio
pip install --global-option='build_ext' \
    --global-option='-I/opt/homebrew/include' \
    --global-option='-L/opt/homebrew/lib' \
    pyaudio
```

Or for Intel Macs:
```bash
brew install portaudio
pip install --global-option='build_ext' \
    --global-option='-I/usr/local/include' \
    --global-option='-L/usr/local/lib' \
    pyaudio
```

### "Permission Denied" Errors

macOS Gatekeeper may block unsigned binaries.

**Solution:**
```bash
# Give execute permissions
chmod +x piper_engine/piper/piper  # If using Piper

# Allow in Security & Privacy
# System Preferences → Security & Privacy → General
# Click "Allow Anyway" next to the blocked app
```

### Microphone Not Working

1. **Check System Preferences**
   - System Preferences → Sound → Input
   - Select correct microphone
   - Adjust input volume

2. **Grant Permissions**
   - System Preferences → Security & Privacy → Privacy → Microphone
   - Enable for Terminal/Python

3. **Test Microphone**
   ```bash
   # Record 3 seconds
   sox -d test.wav trim 0 3
   # Play it back
   afplay test.wav
   ```

### "Symbol not found" Error (M1/M2 Macs)

Some packages need ARM-specific builds on Apple Silicon.

**Solution:**
```bash
# Reinstall with native builds
pip uninstall numpy
pip install --no-cache-dir numpy

# Or use Rosetta 2 (not recommended)
arch -x86_64 /bin/bash
python3 -m venv venv
```

### UI Window Doesn't Appear

```bash
# Reinstall PyQt6 with Homebrew Qt
brew install qt@6
pip install --force-reinstall --no-cache-dir PyQt6
```

## Performance Optimization

### Use Faster Model

Edit `core/listening.py`:
```python
self.model_size = "tiny.en"  # Faster
```

### Use GPU (M1/M2 Only)

Apple Silicon Macs can use GPU acceleration:

```bash
# Install PyTorch with Metal support
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu
```

Edit `core/listening.py`:
```python
device = "mps"  # Metal Performance Shaders
compute_type = "float16"
```

### Adjust Voice Speed

Edit `data/user_config.json`:
```json
{
  "voice_rate": 175,
  "voice_volume": 1.0
}
```

## Startup on Login

### Method 1: Login Items

1. Go to **System Preferences** → **Users & Groups**
2. Select your user → **Login Items**
3. Click **+** and add the startup script

Create `start_sunday.command`:
```bash
#!/bin/bash
cd ~/Sunday-final-year
source venv/bin/activate
python main.py
```

Make it executable:
```bash
chmod +x start_sunday.command
```

### Method 2: LaunchAgent

Create `~/Library/LaunchAgents/com.sunday.assistant.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sunday.assistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/Sunday-final-year/venv/bin/python</string>
        <string>/Users/YOUR_USERNAME/Sunday-final-year/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/Sunday-final-year</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.sunday.assistant.plist
```

## macOS-Specific Features

Sunday supports macOS-specific commands:

| Say This | Action |
|----------|--------|
| "Lock computer" | Locks the Mac |
| "Sleep computer" | Puts Mac to sleep |
| "Open System Preferences" | Opens preferences |
| "Show desktop" | F11 or Mission Control |

## Compatibility Notes

### Intel vs Apple Silicon (M1/M2/M3)

Sunday works on both architectures. Apple Silicon offers better performance and battery life.

Some packages install faster on Intel due to better pre-built wheels.

### macOS Versions

- **macOS 11 Big Sur**: Fully supported
- **macOS 12 Monterey**: Fully supported
- **macOS 13 Ventura**: Fully supported
- **macOS 14 Sonoma**: Fully supported

## Troubleshooting

### "SSL: CERTIFICATE_VERIFY_FAILED"

Download certificates:
```bash
/Applications/Python\ 3.11/Install\ Certificates.command
```

### Homebrew Path Issues

Add to `~/.zshrc` or `~/.bash_profile`:
```bash
# For Apple Silicon
eval "$(/opt/homebrew/bin/brew shellenv)"

# For Intel
eval "$(/usr/local/bin/brew shellenv)"
```

### Virtual Environment Activation

If `source venv/bin/activate` fails:
```bash
# Use full path
source ~/Sunday-final-year/venv/bin/activate

# Or use Python directly
~/Sunday-final-year/venv/bin/python main.py
```

## Advanced Configuration

### Custom Python Version

Use pyenv for version management:
```bash
brew install pyenv
pyenv install 3.11.7
pyenv local 3.11.7
python3 -m venv venv
```

### Disk Space Optimization

Models are cached in `~/.cache/huggingface/`:
```bash
# Check size
du -sh ~/.cache/huggingface/

# Clear old models
rm -rf ~/.cache/huggingface/hub/models--*
```

## Uninstallation

```bash
cd Sunday-final-year

# Deactivate if active
deactivate

# Remove virtual environment
rm -rf venv

# Remove cache
rm -rf ~/.cache/huggingface/

# Remove project
cd ..
rm -rf Sunday-final-year
```

## Getting Help

1. Check `data/logs/` for error messages
2. Run with verbose output:
   ```bash
   python main.py --verbose
   ```
3. Check system logs:
   ```bash
   log show --predicate 'process == "Python"' --last 1h
   ```
4. File an issue on GitHub with:
   - macOS version (About This Mac)
   - Chip (Intel or Apple Silicon)
   - Python version
   - Error messages

---

**Next Steps:**
- Configure workspaces in `data/workspaces.json`
- Try voice commands from [README.md](../README.md)
- Explore macOS-specific TTS voices with `say -v "?"`
