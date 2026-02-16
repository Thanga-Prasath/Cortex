# Sunday Voice Assistant

**A cross-platform AI-powered voice assistant for desktop computers**

Sunday is an intelligent voice assistant that runs on **Windows, Linux, and macOS**. It uses state-of-the-art AI models for speech recognition and natural language understanding, providing a powerful hands-free computing experience.

## ✨ Key Features

- 🎤 **Voice-Activated Commands** - Control your computer with natural language
- 🧠 **AI-Powered Understanding** - Smart intent recognition using machine learning
- 🗣️ **Text-to-Speech** - Natural voice responses with multiple TTS engine support
- 📁 **File Management** - Create, move, delete files and folders by voice
- 🖥️ **System Control** - Launch apps, manage windows, check system info
- 🔒 **Security Tools** - System scans, firewall checks, port monitoring
- 📊 **System Monitoring** - CPU, memory, disk usage tracking
- 💼 **Workspace Management** - Quick access to your project directories
- 🌐 **Cross-Platform** - Works on Windows, Linux, and macOS

## 🖥️ Platform Support

| Feature | Windows | Linux | macOS |
|---------|---------|-------|-------|
| Voice Recognition | ✅ | ✅ | ✅ |
| Text-to-Speech | ✅ | ✅ | ✅ |
| UI Interface | ✅ | ✅ | ✅ |
| File Manager Integration | ✅ (Explorer) | ✅ (Multiple) | ⚠️ (Basic) |
| System Control | ✅ | ✅ | ✅ |
| Workspace Management | ✅ | ✅ | ✅ |

**Legend:** ✅ Full Support | ⚠️ Basic Support | ❌ Not Available

## 📋 System Requirements

### All Platforms
- **Python**: 3.9 or higher (3.10+ recommended)
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: ~2GB for models and dependencies
- **Microphone**: Required for voice input
- **Audio Output**: Required for voice responses

### Platform-Specific
- **Windows**: Windows 10 or higher
- **Linux**: Any modern distribution (Ubuntu 20.04+, Fedora 35+, etc.)
- **macOS**: macOS 11 Big Sur or higher

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Thanga-Prasath/Sunday-final-year.git
cd Sunday-final-year
```

### 2. Run Setup Script

The setup script automatically detects your operating system and installs the correct dependencies:

**Windows:**
```cmd
python setup.py
```

**Linux/macOS:**
```bash
python3 setup.py
```

This will:
- Create a virtual environment
- Install platform-specific dependencies
- Download AI models (first time only)
- Set up data directories

### 3. Activate Virtual Environment

**Windows:**
```cmd
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 4. Run Sunday

```bash
python main.py
```

Or on Windows, simply double-click `start.bat`

## 📖 Documentation

- **[INSTALL.md](INSTALL.md)** - Detailed installation guide
- **[docs/linux-setup.md](docs/linux-setup.md)** - Linux-specific setup
- **[docs/windows-setup.md](docs/windows-setup.md)** - Windows-specific setup
- **[docs/macos-setup.md](docs/macos-setup.md)** - macOS-specific setup

## 🎯 Usage Examples

| Say This | Sunday Does |
|----------|-------------|
| "What time is it?" | Tells the current time |
| "Open Chrome" | Launches Google Chrome |
| "System information" | Shows CPU, RAM, disk usage |
| "Create folder Projects" | Creates a new folder |
| "Move selected files to Documents" | Moves files (file manager integration) |
| "Lock computer" | Locks the system |
| "Minimize window" | Minimizes active window |

## 🛠️ Advanced Features

### Workspace Management
Quickly navigate to your frequently used directories:
- "Launch workspace Sunday" - Opens your project directory
- "Show workspaces" - Lists all configured workspaces

### System Monitoring
- "Check CPU usage"
- "Memory status"
- "Disk space"
- "Show running processes"

### Security
- "Security scan"
- "Check firewall status"
- "Show open ports"

## 🔧 Configuration

Configuration files are located in the `data/` directory:

- `data/user_config.json` - Voice settings, UI preferences
- `data/workspaces.json` - Workspace definitions
- `data/apps.json` - Application mappings

## 🐛 Troubleshooting

### Microphone Not Working
- **Windows**: Check Privacy Settings > Microphone permissions
- **Linux**: Verify ALSA/PulseAudio configuration
- **macOS**: Grant microphone access in System Preferences > Security & Privacy

### TTS Not Speaking
- Verify audio output device is working
- Check volume settings in `data/user_config.json`
- Try different TTS engines (Piper vs pyttsx3)

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements-<your-os>.txt --force-reinstall
```

For more issues, see [INSTALL.md](INSTALL.md#troubleshooting)

## 🏗️ Technology Stack

- **Speech Recognition**: [faster-whisper](https://github.com/guillaumekln/faster-whisper) (OpenAI Whisper)
- **NLU**: Custom intent classifier with scikit-learn
- **TTS**: [Piper](https://github.com/rhasspy/piper) (primary), pyttsx3 (fallback)
- **UI**: PyQt6
- **Audio**: PyAudio

## 📝 License

This project is for educational purposes. See LICENSE file for details.

## 🤝 Contributing

This is a final year project. Contributions, suggestions, and feedback are welcome!

## 👨‍💻 Author

**Thanga Prasath**

- GitHub: [@Thanga-Prasath](https://github.com/Thanga-Prasath)
- Repository: [Sunday-final-year](https://github.com/Thanga-Prasath/Sunday-final-year)

## 🙏 Acknowledgments

- OpenAI for the Whisper speech recognition model
- Rhasspy project for Piper TTS
- The Python community for excellent libraries

---

**Note**: This assistant works best with clear speech in a quiet environment. Speak naturally and wait for the listening indicator before giving commands.
