<p align="center">
  <img src="balkgrab/Icons/icon_256x256.png" alt="BalkGrab Logo" width="128"/>
</p>

<h1 align="center">BalkGrab</h1>

<p align="center">
  <strong>Free & Open Source YouTube Downloader</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.4.0-green?style=for-the-badge" alt="Version"/>
  <img src="https://img.shields.io/badge/python-3.9+-blue?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/PySide6-Qt-41CD52?style=for-the-badge&logo=qt" alt="PySide6"/>
  <img src="https://img.shields.io/badge/license-MIT-orange?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/badge/platform-Linux-lightgrey?style=for-the-badge&logo=linux" alt="Platform"/>
  <br>
  <img src="https://img.shields.io/badge/Built_with-Claude_Code_AI-blueviolet?style=for-the-badge&logo=anthropic" alt="Built with Claude Code"/>
</p>

---

## Screenshots

| Search & Preview | Downloads |
|:---:|:---:|
| ![Search](.github/screenshots/search.png) | ![Downloads](.github/screenshots/downloads.png) |

| Settings | About |
|:---:|:---:|
| ![Settings](.github/screenshots/settings.png) | ![About](.github/screenshots/about.png) |

---

## Features

- **YouTube Search** - Search directly from the app
- **Direct URL Support** - Paste any YouTube link
- **Playlist Support** - Load and batch download playlists
- **Clipboard Detection** - Auto-detects YouTube URLs from clipboard
- **Live Preview** - Stream and preview before downloading
- **Video Downloads** - 4K, 2K, 1080p, 720p, 480p, 360p, 240p
- **Audio Downloads** - MP3, AAC, FLAC, WAV, OGG with conversion
- **Built-in Media Player** - Play downloaded files instantly
- **File Conversion** - Right-click to convert downloaded files (MP3, MP4, FLAC, WAV, OGG, AAC)
- **Multi-Language** - English, Deutsch, Hrvatski/Srpski
- **Themes** - BalkGrab Dark, Nord, Dracula, Catppuccin Mocha, Gruvbox, Arc Dark, Tokyo Night, or System Default
- **System Tray** - Minimize to tray, background playback, desktop notifications
- **Browser Cookies** - Auto-detect browser for age-restricted content

---

## Installation

### Quick Install (Recommended)

```bash
git clone https://github.com/NeleBiH/BalkGrab.git
cd BalkGrab
./balkgrab/setup_BalkGrab.sh
```

Choose **1) Install / Update** from the menu. The setup script will:
- Detect your distro and install system dependencies (`python3`, `ffmpeg`) via `pacman` / `apt` / `dnf` / `zypper` / `xbps` / `emerge` / `apk`
- Create a Python virtualenv at `~/.balkgrab/.venv` and install `PySide6`, `yt-dlp`, `requests`
- Copy the `balkgrab` package to `~/.balkgrab/` and create a launcher
- Install icons and create a menu entry (works on GNOME, KDE, XFCE, MATE, Cinnamon, LXDE and others)
- Install deno (needed for YouTube downloads)

After installation, find **BalkGrab** in your application menu or run `balkgrab` from terminal.

### Updating

Run the setup script again and choose **1) Install / Update**. Your settings and download history are always preserved.

### Run from Source (without installing)

```bash
git clone https://github.com/NeleBiH/BalkGrab.git
cd BalkGrab
python3 -m venv .venv
.venv/bin/pip install PySide6 yt-dlp requests
.venv/bin/python -m balkgrab
```

---

## Uninstallation

```bash
./balkgrab/setup_BalkGrab.sh   # Choose 2) Uninstall
```

Your settings and download history are kept by default (you will be asked).

---

## Usage

1. **Search** - Type a search query or paste a YouTube URL
2. **Preview** - Click Play to preview the video/audio
3. **Select Format** - Choose Video or Audio
4. **Select Quality** - Pick your preferred quality
5. **Download** - Click the download button!

For playlists, paste the playlist URL and choose how many videos to load (first 20/50/100 or all).

---

## Settings

Access settings via the **Settings** tab.

| Setting | Description |
|---------|-------------|
| **Language** | Switch between English, Deutsch, Hrvatski/Srpski. Requires restart. |
| **Theme** | Choose from 7 dark themes or use System Default |
| **Show system tray icon** | Display BalkGrab icon in the system tray |
| **Minimize to system tray** | Minimize to tray instead of closing |
| **Continue playing in tray** | Keep playing audio when minimized to tray |
| **Start minimized** | Launch the app minimized to tray |
| **Show download notifications** | Desktop notifications when downloads complete |
| **Download location** | Choose where files are saved (default: `~/Downloads`) |
| **Browser cookies** | Auto-detected. Used for age-restricted videos and to avoid bot detection. |
| **Simultaneous downloads** | Number of parallel downloads (1-10) |
| **Auto-play after download** | Automatically play files after download completes |
| **Video player** | Set default external player for video files (VLC, MPV, etc.) |

---

## Project Structure

```
BalkGrab/
├── balkgrab/               # Main application package
│   ├── __init__.py         # Version and app name
│   ├── __main__.py         # Entry point (python -m balkgrab)
│   ├── app.py              # Main window and UI
│   ├── workers.py          # Background workers (search, download, thumbnail)
│   ├── models.py           # Data models and signals
│   ├── widgets.py          # Custom Qt widgets
│   ├── constants.py        # Paths and constants
│   ├── translations.py     # Multi-language support (EN/DE/HR)
│   ├── themes.py           # Theme definitions (easy to add new themes)
│   ├── Icons/              # Application icons (all sizes)
│   └── setup_BalkGrab.sh   # Install/update/uninstall script
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Known Limitations

- **Preview may stall on long videos** - YouTube stream URLs expire after a few minutes. The app auto-detects stalls and refreshes the stream, but brief interruptions may occur. This is a YouTube-side limitation.
- **deno required for downloads** - YouTube requires JavaScript challenge solving. Install deno (`curl -fsSL https://deno.land/install.sh | sh`) or use the setup script which installs it automatically.

---

## Troubleshooting

### "Requested format is not available" or "Signature solving failed"

Make sure deno is installed and yt-dlp is up to date:
```bash
curl -fsSL https://deno.land/install.sh | sh   # Install deno
~/.balkgrab/.venv/bin/pip install --upgrade yt-dlp   # Update yt-dlp
```

### "Could not find cookies database"

Go to **Settings** and set the correct browser under **Browser cookies**. The app auto-detects your browser on first run.

### Audio conversion not working

Make sure ffmpeg is available:
```bash
ffmpeg -version
```

### Video won't play (Linux)

```bash
sudo pacman -S vlc   # Arch
sudo apt install vlc # Debian/Ubuntu
```

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Acknowledgements

BalkGrab wouldn't be possible without these amazing open source projects:

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - The powerful media downloader that powers all downloads
- **[PySide6](https://doc.qt.io/qtforpython-6/)** - Qt for Python, the GUI framework
- **[FFmpeg](https://ffmpeg.org/)** - Audio/video conversion engine
- **[deno](https://deno.land/)** - JavaScript runtime for YouTube challenge solving
- **[Requests](https://github.com/psf/requests)** - HTTP library for Python

Thank you to all the contributors and maintainers of these projects!

---

## Author

**NeleBiH** - [GitHub](https://github.com/NeleBiH)

> This application was built with [Claude Code](https://claude.ai/claude-code) (Anthropic's AI coding assistant).

---

