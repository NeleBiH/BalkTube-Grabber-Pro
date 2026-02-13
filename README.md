<p align="center">
  <img src="Icons/icon_256x256.png" alt="BalkGrab Logo" width="128"/>
</p>

<h1 align="center">BalkGrab</h1>

<p align="center">
  <strong>Free & Open Source YouTube Downloader</strong><br>
  <em>Inspired by ClipGrab - Made for the Balkans</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.2-green?style=for-the-badge" alt="Version"/>
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
<img width="1098" height="931" alt="Screenshot_20260202_210236" src="https://github.com/user-attachments/assets/4971339a-ec6a-45bd-9974-bcda6fe694c5" />
<img width="1098" height="931" alt="Screenshot_20260202_210249" src="https://github.com/user-attachments/assets/8576e3ec-9fa2-4518-8740-ef641a2385cb" />
<img width="1098" height="931" alt="Screenshot_20260202_210256" src="https://github.com/user-attachments/assets/09d2a1e1-656c-4a63-a87c-0e89fae223d2" />
</p>

---

## Features

- **YouTube Search** - Search directly from the app
- **Direct URL Support** - Paste any YouTube link
- **Live Preview** - Stream and preview before downloading
- **Video Downloads** - 4K, 2K, 1080p, 720p, 480p, 360p, 240p
- **Audio Downloads** - MP3, AAC, FLAC, WAV, OGG
- **Built-in Media Player** - Play downloaded files instantly
- **Multi-Language** - English, Deutsch, Hrvatski/Srpski
- **Dark Theme** - Modern UI with system tray support

---

## Installation

### Linux (Recommended)

```bash
git clone https://github.com/NeleBiH/BalkGrab.git
cd BalkGrab
./setup.sh
```

Choose **1) Install / Update** from the menu. This will:
- Install the program to `~/.balkgrab/`
- Set up Python virtual environment with all dependencies
- Install icons and create a menu entry
- Clean up any old versions (BalkTube Grabber, etc.)

After installation, find **BalkGrab** in your application menu!

### Linux (Run Without Installing)

```bash
git clone https://github.com/NeleBiH/BalkGrab.git
cd BalkGrab
./run.sh
```

### Windows

Download **BalkGrab.exe** from the [Releases](https://github.com/NeleBiH/BalkGrab/releases) page.

> **Note:** FFmpeg is required for audio conversion. Download from https://ffmpeg.org and add to PATH.

### Manual (Any Platform)

```bash
python3 -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

pip install PySide6 yt-dlp requests
pip install --upgrade --pre yt-dlp

python BalkGrab.py
```

---

## Requirements

- **Python 3.9+**
- **FFmpeg** (for audio conversion)

```bash
# Arch/Manjaro
sudo pacman -S ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

---

## Uninstallation

```bash
./setup.sh
```

Choose **2) Uninstall** from the menu. This removes the program, icons, menu entry, settings, and cleans up any old versions.

---

## Usage

1. **Search** - Type a search query or paste a YouTube URL
2. **Preview** - Click Play to preview the video/audio
3. **Select Format** - Choose Video or Audio
4. **Select Quality** - Pick your preferred quality
5. **Download** - Click the download button!

---

## Troubleshooting

### "Signature extraction failed" or 403 errors
```bash
pip install --upgrade --pre yt-dlp
```

### Audio conversion not working
```bash
ffmpeg -version  # Make sure FFmpeg is installed
```

### Video won't play (Linux)
```bash
sudo pacman -S vlc  # or mpv
```

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Author

**NeleBiH** - [GitHub](https://github.com/NeleBiH)

> This application was built with [Claude Code](https://claude.ai/claude-code) (Anthropic's AI coding assistant).

---

<p align="center">
  Made with love for the Balkan community
</p>
