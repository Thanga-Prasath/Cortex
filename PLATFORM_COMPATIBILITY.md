# Platform Compatibility Matrix

## Overview

Sunday Voice Assistant is designed to work across **Windows, Linux, and macOS**. This document details which features work on each platform and any platform-specific considerations.

## Legend

- ✅ **Fully Supported** - Works out of the box
- ⚠️ **Partial Support** - Works with limitations or requires additional setup
- ❌ **Not Supported** - Feature not available on this platform
- 🔄 **Auto-Install** - Dependency auto-installed if missing (Linux only)

---

## Core Features

| Feature | Windows | Linux | macOS | Notes |
|---------|---------|-------|-------|-------|
| **Voice Recognition** | ✅ | ✅ | ✅ | Whisper works everywhere |
| **Text-to-Speech** | ✅ | ✅ | ✅ | pyttsx3 + Piper support |
| **Wake Word** | ✅ | ✅ | ✅ | OpenWakeWord compatible |
| **UI (PyQt6)** | ✅ | ✅ | ✅ | Cross-platform GUI |

---

## System Control Features

### Power Management

| Function | Windows | Linux | macOS | Implementation |
|----------|---------|-------|-------|----------------|
| Lock Screen | ✅ | ✅ | ✅ | rundll32 / gnome-screensaver / pmset |
| Sleep | ✅ | ✅ | ✅ | powrprof.dll / systemctl / pmset |
| Restart | ✅ | ✅ | ✅ | shutdown /r / systemctl / shutdown -r |
| Shutdown | ✅ | ✅ | ✅ | shutdown /s / systemctl / shutdown -h |

**File:** `components/system/power.py`

### Volume Control

| Function | Windows | Linux | macOS | Implementation |
|----------|---------|-------|-------|----------------|
| Set Volume | ✅ | ✅ | ✅ | SendKeys / pactl / osascript |
| Mute | ✅ | ✅ | ✅ | SendKeys / pactl / osascript |
| Unmute | ✅ | ✅ | ✅ | SendKeys / pactl / osascript |

**File:** `components/system/volume.py`

### Network Management

| Function | Windows | Linux | macOS | Implementation |
|----------|---------|-------|-------|----------------|
| WiFi List | ✅ | ✅ | ✅ | netsh / nmcli / airport |
| WiFi Password | ⚠️ | ✅ | ⚠️ | See limitations |

**File:** `components/system/wifi.py`, `wifi_password.py`

---

## File Manager Integration

| Feature | Windows | Linux | macOS | Implementation |
|---------|---------|-------|-------|----------------|
| Selected File Detection | ✅ | ✅ 🔄 | ⚠️ | PowerShell COM / D-Bus+xdotool / Clipboard |

**File:** `components/file_manager/detection.py`

**Platform Details:**
- **Windows**: PowerShell + COM (Shell.Application) - works automatically
- **Linux**: D-Bus (KDE/GNOME) + xdotool/xclip fallback 🔄 (auto-installed)
- **macOS**: Basic clipboard method

---

## Security Features

| Feature | Windows | Linux | macOS | Implementation |
|---------|---------|-------|-------|----------------|
| Security Scan | ✅ | ✅ 🔄 | ⚠️ | Windows Defender / ClamAV / Gatekeeper |

**File:** `components/system/security.py`

**Platform Details:**
- **Windows**: Windows Security Center + Defender Quick Scan
- **Linux**: rkhunter or ClamAV 🔄 (auto-installed with freshclam)
- **macOS**: Gatekeeper + SIP status

---

## Installation Features

| Feature | Windows | Linux | macOS | Status |
|---------|---------|-------|-------|--------|
| Python Version Check | ✅ | ✅ | ✅ | 3.9+ required |
| Virtual Environment | ✅ | ✅ | ✅ | Automatic |
| Dependency Installation | ✅ | ✅ | ✅ | Platform-specific |
| Config File Creation | ✅ | ✅ | ✅ | Automatic |
| Post-Install Verification | ✅ | ✅ | ✅ | PyAudio + Whisper |
| Auto-Dependency Install | ❌ | ✅ | ❌ | Linux: apt/dnf/yum/pacman |

**File:** `setup.py`

---

## Known Limitations

### Windows
- No auto-dependency installation (manual install required)
- Volume control uses keyboard simulation

### Linux
- File manager integration requires xdotool/xclip (auto-installed)
- Security scan requires ClamAV (auto-installed)
- Wayland has limited xdotool support

### macOS
- File manager integration uses basic clipboard method
- No auto-dependency installation (manual Homebrew install)
- Some permissions required (Microphone, Accessibility)

---

## Dependency Summary

### Platform-Specific Python Packages
- **Windows**: `winshell` (Recycle Bin)
- **Linux**: None (all standard)
- **macOS**: `pyobjc-framework-Cocoa` (system integration)

### Platform-Specific System Tools
- **Linux**: `xdotool` 🔄, `xclip` 🔄, `clamav` 🔄 (all auto-installed)
- **macOS**: `portaudio` (install via: `brew install portaudio`)
- **Windows**: No additional tools needed

---

## Testing Status

✅ **Linux** - Fully tested and verified
⏳ **Windows** - Code implemented, needs user testing
⏳ **macOS** - Code implemented, needs user testing
