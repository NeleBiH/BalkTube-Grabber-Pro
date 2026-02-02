# 🎵 BalkTube Grabber Pro - Agent Guide

This document provides essential information for agents working with the BalkTube Grabber Pro codebase.

## 📁 Project Overview

A PySide6-based YouTube downloader with integrated media player, featuring:
- Search and download functionality
- Video/audio format conversion
- Built-in media player
- Multi-language support (EN/DE/HR)
- System tray integration
- Dark theme UI

## 🚀 Essential Commands

### Development
```bash
# Run the application
python "BalkTube Grabber Pro.py"

# Install dependencies for development
pip install PySide6 yt-dlp requests Pillow

# Upgrade to latest yt-dlp dev version
pip install --upgrade --pre yt-dlp
```

### Build & Installation
```bash
# Install the application (Linux)
./install.sh

# Uninstall the application
./uninstall.sh

# Manual installation (if needed)
python3 -m venv .venv
source .venv/bin/activate
pip install PySide6 yt-dlp requests Pillow
```

### Requirements
- Python 3.9+
- FFmpeg (for audio conversion)
- Deno (for YouTube signature solving - installed by install.sh)

## 📂 Code Structure

```
BalkTube Grabber Pro/
├── BalkTube Grabber Pro.py  # Main application
├── install.sh               # Installation script
├── uninstall.sh             # Uninstallation script
├── README.md                # Project documentation
├── problemi.txt             # Known issues/todo
├── moguce ideje za buducnost.md # Future ideas
├── Icons/                   # Application icons
└── .venv/                   # Virtual environment (created by installer)
```

## 🧠 Architecture

### Core Components
1. **Main Window** (`BalkTubeGrabber` class)
   - Tab-based interface (Search, Downloads, Settings, About)
   - Settings persistence with QSettings
   - System tray integration

2. **Workers** (Separate threads)
   - `SearchWorker` - YouTube search
   - `ThumbnailWorker` - Async thumbnail loading
   - `DownloadWorker` - Video/audio download with progress tracking

3. **Media Players**
   - Preview player (for streaming before download)
   - Downloaded files player (integrated in Downloads tab)

### Key Classes
- `DownloadItem` - Represents a single download
- `VideoItemWidget` - Custom widget for search results
- `WorkerSignals` - Thread-safe signal communication
- `ClickableSlider` - Custom slider that responds to clicks

## 🔧 Conventions & Patterns

### Code Style
- Python naming conventions (snake_case for variables/functions, PascalCase for classes)
- Comprehensive logging with logging module
- Qt signal/slot pattern for thread communication
- Translations stored in TRANSLATIONS dictionary

### UI Patterns
- Dark theme with CSS styling
- Tab-based navigation
- Responsive layout with QSplitter
- Custom widgets for media controls
- Multi-language support through tr() method

### Translation System
- Translations stored in TRANSLATIONS dict
- Three languages supported: English, German, Croatian
- get_text() method handles dynamic text with parameters

## 🧪 Testing Approach

### Manual Testing
- UI interaction testing
- Download functionality with various formats
- Media player functionality
- Settings persistence
- System tray operations

### Known Issues/TODO
Check `problemi.txt` for current issues and `moguce ideje za buducnost.md` for future enhancements.

## ⚠️ Important Gotchas

1. **Threading**: All network operations must run in separate threads to avoid blocking the UI
2. **Translations**: Always use get_text() method for translatable strings
3. **File Paths**: Use APP_DIR for consistent path handling
4. **yt-dlp**: Requires regular updates for YouTube compatibility
5. **FFmpeg**: Required dependency for audio conversion - always check availability
6. **Deno**: Needed for YouTube signature solving - installed by install.sh

## 🛠️ Dependencies

### Core Libraries
- PySide6 (Qt for Python) - UI framework
- yt-dlp - YouTube download backend
- requests - HTTP library for thumbnails
- Pillow - Image processing (if needed)

### System Dependencies
- FFmpeg - Audio/video processing
- Deno - JavaScript runtime for signature solving

## 🌍 Internationalization

The application supports three languages:
- English (en)
- German (de)
- Croatian/Serbian (hr)

Translations are managed in the TRANSLATIONS dictionary in the main .py file.

## 🎨 UI/UX Guidelines

1. Maintain dark theme consistency
2. Use descriptive status messages
3. Ensure all buttons have clear labels
4. Provide visual feedback for long operations
5. Follow platform conventions for system tray
6. Maintain consistent icon usage

## 📈 Future Development Directions

See `moguce ideje za buducnost.md` for comprehensive roadmap including:
- Music player features (playlists, queue, favorites)
- UI enhancements (themes, visualizer)
- Download improvements (batch, metadata)
- Additional platforms (SoundCloud, etc.)
- Mobile/web versions