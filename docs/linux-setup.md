# Linux Setup Guide - Sunday Voice Assistant

This guide covers Linux-specific setup, configuration, and troubleshooting for Sunday.

## Supported Distributions

Sunday has been tested on:
- Ubuntu 20.04 LTS, 22.04 LTS, 24.04 LTS
- Debian 11, 12
- Fedora 35+
- Arch Linux
- Manjaro
- Pop!_OS

Other modern distributions should work as well.

## System Dependencies

### Required Dependencies

These are mandatory for Sunday to work:

**Debian/Ubuntu:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv build-essential portaudio19-dev
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip python3-devel gcc portaudio-devel
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip base-devel portaudio
```

### Optional Dependencies (Recommended)

These enhance functionality but aren't strictly required:

**File Manager Integration:**
```bash
# Debian/Ubuntu
sudo apt install xdotool xclip

# Fedora
sudo dnf install xdotool xclip

# Arch Linux
sudo pacman -S xdotool xclip
```

With these tools, Sunday can detect files you've selected in your file manager (Nautilus, Dolphin, Thunar, etc.) for voice-controlled file operations.

## Audio Configuration

### ALSA Configuration

Most modern distributions have ALSA configured correctly by default. To verify:

```bash
# List audio devices
arecord -l

# Test recording
arecord -d 3 test.wav
aplay test.wav
```

### PulseAudio/PipeWire

If you're using PulseAudio or PipeWire (most modern distros):

```bash
# Check PulseAudio status
pactl info

# List input devices
pactl list sources short

# Adjust microphone volume
pavucontrol  # GUI tool
```

### Permissions

Ensure your user is in the `audio` group:

```bash
groups $USER
# Should include 'audio'

# If not, add it:
sudo usermod -aG audio $USER
# Then log out and back in
```

## Installation

### Quick Install

```bash
# Clone repository
git clone https://github.com/Thanga-Prasath/Sunday-final-year.git
cd Sunday-final-year

# Run setup
python3 setup.py

# Activate environment
source venv/bin/activate

# Run Sunday
python main.py
```

### Manual Installation

If the automatic setup fails:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements-linux.txt

# Download Whisper model
python -c "from faster_whisper import WhisperModel; WhisperModel('base.en')"

# Run Sunday
python main.py
```

## Piper TTS Setup (Optional)

Piper provides higher quality text-to-speech than the default pyttsx3.

### Enable Piper

The Piper binary is included in `piper_engine/piper/`. Make it executable:

```bash
chmod +x piper_engine/piper/piper
```

Sunday will automatically use Piper if it's available and executable.

### Verify Piper

Test Piper directly:

```bash
echo "Hello from Piper" | piper_engine/piper/piper \
  --model piper_engine/voice.onnx \
  --output_raw | aplay -r 22050 -f S16_LE -t raw
```

If you hear speech, Piper is working correctly!

### Alternative Voice Models

Download additional voices from [Piper Releases](https://github.com/rhasspy/piper/releases):

```bash
# Example: Download a different voice
cd piper_engine
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/voice-en-us-libritts-high.tar.gz
tar -xzf voice-en-us-libritts-high.tar.gz

# Rename to voice.onnx
mv en_US-libritts-high.onnx voice.onnx
```

## Desktop Environment Integration

### File Manager Detection

Sunday supports these file managers out of the box:
- **Dolphin** (KDE) - via D-Bus
- **Nautilus** (GNOME) - via D-Bus  
- **Thunar** (Xfce) - via clipboard
- **Nemo** (Cinnamon) - via clipboard
- **PCManFM** (LXDE) - via clipboard

No additional configuration needed if you have `xdotool` and `xclip` installed.

### System Tray Integration

The UI window should appear in your system tray automatically with:
- KDE Plasma
- GNOME (with TopIcons extension)
- Xfce
- MATE
- Cinnamon

## Common Issues

### PyAudio Installation Fails

**Error:**
```
error: portaudio.h: No such file or directory
```

**Solution:**
```bash
# Debian/Ubuntu
sudo apt install portaudio19-dev

# Fedora
sudo dnf install portaudio-devel

# Arch
sudo pacman -S portaudio

# Then reinstall
pip install --force-reinstall pyaudio
```

### "ALSA lib ... Unknown PCM" Errors

These are warnings from ALSA and can usually be ignored. Sunday suppresses them automatically, but if they still appear:

**Solution 1: Create ALSA config**
```bash
cat > ~/.asoundrc << 'EOF'
pcm.!default {
    type pulse
}
ctl.!default {
    type pulse
}
EOF
```

**Solution 2: Use PulseAudio**
```bash
sudo apt install pulseaudio
pulseaudio --start
```

### Microphone Permissions (Snap/Flatpak)

If using Snap or Flatpak Python:

```bash
# For Snap
snap connect <app> :audio-record

# Use system Python instead:
sudo apt install python3-pip
```

### UI Window Doesn't Appear

**Check PyQt6:**
```bash
pip install --force-reinstall PyQt6
```

**Try Wayland/X11:**
```bash
# Try with X11
export QT_QPA_PLATFORM=xcb
python main.py

# Or try Wayland
export QT_QPA_PLATFORM=wayland
python main.py
```

### xdotool: command not found

```bash
# Debian/Ubuntu
sudo apt install xdotool xclip

# Fedora
sudo dnf install xdotool xclip

# Arch
sudo pacman -S xdotool xclip
```

## Performance Tuning

### Faster Whisper (Lower Quality)

Edit `core/listening.py`:
```python
self.model_size = "tiny.en"  # Fastest
```

### Better Whisper (Slower)

```python
self.model_size = "small.en"  # More accurate
```

### GPU Acceleration (NVIDIA)

If you have an NVIDIA GPU:

```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Edit core/listening.py:
# device="cuda"
# compute_type="float16"
```

### Reduce Background Noise

Adjust threshold in `core/listening.py`:
```python
self.THRESHOLD = 500  # Higher = less sensitive
```

## Security Considerations

### Firewall

Sunday doesn't require network access except for initial model downloads.

```bash
# Optional: Block after setup
sudo ufw deny out from any to any app Sunday
```

### Sandboxing

Run in a limited environment:

```bash
firejail --net=none python main.py
```

## Systemd Service (Autostart)

Create a systemd user service to auto-start Sunday:

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/sunday.service << 'EOF'
[Unit]
Description=Sunday Voice Assistant
After=sound.target

[Service]
Type=simple
WorkingDirectory=/path/to/Sunday-final-year
ExecStart=/path/to/Sunday-final-year/venv/bin/python main.py
Restart=on-failure

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user enable sunday.service
systemctl --user start sunday.service

# Check status
systemctl --user status sunday.service
```

## Wayland vs X11

Sunday works on both X11 and Wayland, but some features have limitations:

| Feature | X11 | Wayland |
|---------|-----|---------|
| Voice Recognition | ✅ | ✅ |
| UI Display | ✅ | ✅ |
| Window Management | ✅ | ⚠️ Limited |
| File Selection (xdotool) | ✅ | ❌ |

On Wayland, use D-Bus file manager integration (Dolphin/Nautilus) for best results.

## Uninstallation

```bash
cd Sunday-final-year

# Deactivate if active
deactivate

# Remove virtual environment
rm -rf venv

# Remove user data (optional)
rm -rf data/

# Remove the project
cd ..
rm -rf Sunday-final-year
```

## Getting Help

1. Check `data/logs/` for error messages
2. Run with verbose output: `python main.py --verbose`
3. File an issue on GitHub with:
   - Linux distribution and version
   - Python version
   - Error messages
   - Audio configuration

---

**Next Steps:**
- Configure workspaces in `data/workspaces.json`
- Customize voice speed in `data/user_config.json`
- Try advanced commands from [README.md](../README.md)
