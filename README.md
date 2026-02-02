<p align="center">
  <img src="Icons/icon_256x256.png" alt="BalkTube Logo" width="128"/>
</p>

<h1 align="center">BalkTube Grabber Pro</h1>

<p align="center">
  <strong>Free & Open Source YouTube Downloader</strong><br>
  <em>Inspired by ClipGrab - Made for the Balkans</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0_Alpha-green?style=for-the-badge" alt="Version"/>
  <img src="https://img.shields.io/badge/python-3.9+-blue?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/PySide6-Qt-41CD52?style=for-the-badge&logo=qt" alt="PySide6"/>
  <img src="https://img.shields.io/badge/license-MIT-orange?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/badge/platform-Linux%20|%20Windows-lightgrey?style=for-the-badge&logo=linux" alt="Platform"/>
  <br>
  <img src="https://img.shields.io/badge/Built_with-Claude_Code_AI-blueviolet?style=for-the-badge&logo=anthropic" alt="Built with Claude Code"/>
</p>

---

## Screenshots

<p align="center">
<img width="1098" height="931" alt="Screenshot_20260202_210220" src="https://github.com/user-attachments/assets/84e455b6-1340-4b91-8af4-3bbe515269cf" />
<img width="1098" height="931" alt="Screenshot_20260202_210256" src="https://github.com/user-attachments/assets/09d2a1e1-656c-4a63-a87c-0e89fae223d2" />
<img width="1098" height="931" alt="Screenshot_20260202_210249" src="https://github.com/user-attachments/assets/8576e3ec-9fa2-4518-8740-ef641a2385cb" />
<img width="1098" height="931" alt="Screenshot_20260202_210236" src="https://github.com/user-attachments/assets/4971339a-ec6a-45bd-9974-bcda6fe694c5" />

</p>

---

## Features

### Search & Preview
- **YouTube Search** - Search directly from the app
- **Direct URL Support** - Paste any YouTube link
- **Live Preview** - Stream and preview before downloading
- **Seek & Volume Control** - Full playback controls

### Download Options
| Video Formats | Audio Formats |
|--------------|---------------|
| 4K (2160p) | MP3 (128-320kbps) |
| 2K (1440p) | AAC (192-256kbps) |
| Full HD (1080p) | FLAC (lossless) |
| HD (720p) | WAV (lossless) |
| 480p, 360p, 240p | OGG (192-320kbps) |

### Built-in Media Player
- Play downloaded audio files instantly
- Seek bar with time display
- Volume control
- External player support for video files

### Multi-Language Support
- English
- Deutsch
- Hrvatski/Srpski

### Modern UI
- Dark theme
- Responsive design
- System tray support
- Desktop notifications

---

## Installation

### Method 1: Quick Install (Linux - Recommended)

```bash
# Clone the repository
git clone https://github.com/NeleBiH/BalkTube-Grabber-Pro.git
cd BalkTube-Grabber-Pro

# Run the installer
./install.sh
```

The installer will:
- Install the program to `~/.balktube/`
- Set up a Python virtual environment with all dependencies
- Install icons to your system
- Create a menu entry (works with KDE, GNOME, XFCE, etc.)
- Install [deno](https://deno.land/) for YouTube signature solving

After installation, find **BalkTube Grabber Pro** in your application menu!

### Method 2: Run Without Installing (Linux)

```bash
# Clone the repository
git clone https://github.com/NeleBiH/BalkTube-Grabber-Pro.git
cd BalkTube-Grabber-Pro

# Run directly (auto-creates venv on first run)
./run.sh
```

### Method 3: AppImage (Linux)

```bash
# Build standalone AppImage (includes Python + all dependencies)
./build-appimage-standalone.sh

# Run the AppImage (no installation needed!)
chmod +x BalkTube_Grabber_Pro-0.1.0-x86_64.AppImage
./BalkTube_Grabber_Pro-0.1.0-x86_64.AppImage
```

**Note:** The AppImage is fully portable (~260MB) - no Python or dependencies needed!

### Method 4: Manual Installation (Linux/Windows/macOS)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install PySide6 yt-dlp requests

# Install latest yt-dlp (recommended)
pip install --upgrade --pre yt-dlp

# Run
python "BalkTube Grabber Pro.py"
```

### Method 5: Windows Standalone EXE

```powershell
# Option A: Run the build script (creates standalone .exe)
.\build-exe.bat

# Option B: PowerShell version
powershell -ExecutionPolicy Bypass -File build-exe.ps1

# The exe will be in: dist\BalkTube Grabber Pro.exe
```

### Method 6: Windows Manual Run

```powershell
# Install dependencies
pip install PySide6 yt-dlp requests

# Download FFmpeg from https://ffmpeg.org and add to PATH

# Run
python "BalkTube Grabber Pro.py"
```

---

## Requirements

- **Python 3.9+**
- **FFmpeg** (for audio conversion)

### Installing FFmpeg

**Arch/Manjaro:**
```bash
sudo pacman -S ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Fedora:**
```bash
sudo dnf install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH.

---

## Uninstallation

### Linux (if installed with install.sh)

```bash
./uninstall.sh
```

This will:
- Remove the program from `~/.balktube/`
- Remove icons from your system
- Remove the menu entry

**Note:** User settings in `~/.config/BalkTube` are preserved. To remove them too:
```bash
rm -rf ~/.config/BalkTube
```

---

## Usage

1. **Search** - Type a search query or paste a YouTube URL
2. **Preview** - Click Play to preview the video/audio
3. **Select Format** - Choose Video or Audio
4. **Select Quality** - Pick your preferred quality
5. **Download** - Click the download button!

---

## Technical Details

- **GUI Framework**: PySide6 (Qt for Python)
- **YouTube Backend**: yt-dlp
- **Audio Conversion**: FFmpeg
- **JavaScript Runtime**: deno (for YouTube signature solving)
- **Architecture**: Multi-threaded with Qt signals/slots
- **Settings**: QSettings (persistent)

### Thread Safety
- SearchWorker - YouTube search
- ThumbnailWorker - Async thumbnail loading
- DownloadWorker - Video/audio download
- Preview streaming runs in background thread

---

## Troubleshooting

### "Signature extraction failed" or 403 errors
YouTube frequently changes their API. Update yt-dlp:
```bash
pip install --upgrade --pre yt-dlp
```

### Audio conversion not working
Make sure FFmpeg is installed and in your PATH:
```bash
ffmpeg -version
```

### App won't start
Ensure you have Python 3.9+ and all dependencies installed:
```bash
python3 --version
pip list | grep -E "PySide6|yt-dlp"
```

### Video won't play (Linux)
Make sure you have a video player installed (VLC, MPV, etc.):
```bash
sudo pacman -S vlc  # Arch
sudo apt install vlc  # Ubuntu/Debian
```

---

## License

MIT License - See [LICENSE](LICENSE) for details.

### Third-Party Licenses
- **PySide6**: LGPL v3
- **yt-dlp**: Unlicense (Public Domain)
- **FFmpeg**: LGPL/GPL
- **deno**: MIT

---

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

---

## Author

**NeleBiH** - [GitHub](https://github.com/NeleBiH)

---

## AI-Generated Code

> **Note:** This application was created with the assistance of [Claude Code](https://claude.ai/claude-code) (Anthropic's AI coding assistant). The code is provided as-is and may require adjustments or improvements over time.

---

Made with love for the Balkan community

<p align="center">
  <strong>Star this repo if you find it useful!</strong>
</p>
