#!/bin/bash
# BalkGrab - Debian/Ubuntu/Mint .deb Package Builder
# NOT TESTED - nemam na cemu da testiram dok ne odradim install Minta

set -e

APP_NAME="balkgrab"
APP_VERSION="0.1.2"
ARCH="amd64"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="/tmp/balkgrab-debbuild"
PKG_NAME="${APP_NAME}_${APP_VERSION}_${ARCH}"
PKG_DIR="${BUILD_DIR}/${PKG_NAME}"

echo "=========================================="
echo "  Building ${APP_NAME} .deb package"
echo "=========================================="
echo ""

# Check dpkg-deb
if ! command -v dpkg-deb &>/dev/null; then
    echo "ERROR: dpkg-deb not found!"
    echo "Install with: sudo apt install dpkg  (on Debian/Ubuntu)"
    echo "         or:  sudo pacman -S dpkg    (on Arch)"
    exit 1
fi

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "[1/5] Creating package structure..."
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/share/$APP_NAME/Icons"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
for size in 16 32 64 128 256; do
    mkdir -p "$PKG_DIR/usr/share/icons/hicolor/${size}x${size}/apps"
done

echo "[2/5] Creating control file..."
cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${APP_VERSION}
Section: multimedia
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.9), python3-pyside6.qtcore, python3-pyside6.qtgui, python3-pyside6.qtwidgets, python3-pyside6.qtmultimedia, yt-dlp, python3-requests, ffmpeg
Recommends: deno
Maintainer: BalkGrab Team <nele@balkgrab.dev>
Homepage: https://github.com/NeleBiH/BalkGrab
Description: YouTube downloader with GUI - ClipGrab alternative
 BalkGrab is a free, open-source YouTube downloader
 inspired by ClipGrab. Download videos in various resolutions or
 convert them to audio formats like MP3, FLAC, and more.
 .
 Features:
  - Search YouTube directly from the app
  - Preview videos before downloading
  - Download videos from 240p to 4K
  - Convert to audio: MP3, AAC, FLAC, WAV, OGG
  - Download manager with progress tracking
  - Built-in media player
  - Multi-language support (EN/DE/HR)
  - System tray integration
EOF

echo "[3/5] Copying application files..."
cp "$SCRIPT_DIR/BalkGrab.py" "$PKG_DIR/usr/share/$APP_NAME/"
cp "$SCRIPT_DIR/Icons/"*.png "$PKG_DIR/usr/share/$APP_NAME/Icons/"
cp "$SCRIPT_DIR/Icons/icon.ico" "$PKG_DIR/usr/share/$APP_NAME/Icons/" 2>/dev/null || true
cp "$SCRIPT_DIR/LICENSE" "$PKG_DIR/usr/share/$APP_NAME/" 2>/dev/null || true

# Install icons to hicolor
for size in 16 32 64 128 256; do
    if [[ -f "$SCRIPT_DIR/Icons/icon_${size}x${size}.png" ]]; then
        cp "$SCRIPT_DIR/Icons/icon_${size}x${size}.png" \
           "$PKG_DIR/usr/share/icons/hicolor/${size}x${size}/apps/${APP_NAME}.png"
    fi
done

# Create launcher script
cat > "$PKG_DIR/usr/bin/$APP_NAME" << 'LAUNCHER'
#!/bin/bash
exec python3 /usr/share/balkgrab/BalkGrab.py "$@"
LAUNCHER
chmod 755 "$PKG_DIR/usr/bin/$APP_NAME"

# Create desktop entry
cat > "$PKG_DIR/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=BalkGrab
GenericName=YouTube Downloader
Comment=Download videos and music from YouTube
Exec=${APP_NAME}
Icon=${APP_NAME}
Terminal=false
Categories=AudioVideo;Audio;Video;Network;
Keywords=youtube;download;music;video;mp3;
StartupWMClass=balkgrab
EOF

echo "[4/5] Creating postinst/postrm scripts..."
cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

cat > "$PKG_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi
EOF
chmod 755 "$PKG_DIR/DEBIAN/postrm"

echo "[5/5] Building .deb package..."
dpkg-deb --build --root-owner-group "$PKG_DIR"

# Copy .deb to project directory
DEB_FILE="${PKG_DIR}.deb"
if [[ -f "$DEB_FILE" ]]; then
    cp "$DEB_FILE" "$SCRIPT_DIR/"
    rm -rf "$BUILD_DIR"
    SIZE=$(du -h "$SCRIPT_DIR/${PKG_NAME}.deb" | cut -f1)
    echo ""
    echo "=========================================="
    echo "  Build successful!"
    echo "=========================================="
    echo ""
    echo "  Package: ${PKG_NAME}.deb"
    echo "  Size: ${SIZE}"
    echo ""
    echo "  Install with:"
    echo "    sudo apt install ./${PKG_NAME}.deb"
    echo ""
    echo "  Or:"
    echo "    sudo dpkg -i ${PKG_NAME}.deb"
    echo "    sudo apt-get install -f   # fix dependencies"
    echo ""
    echo "  NOT TESTED - nemam na cemu da testiram dok ne odradim install Minta"
    echo ""
else
    rm -rf "$BUILD_DIR"
    echo ""
    echo "ERROR: Build failed!"
fi
