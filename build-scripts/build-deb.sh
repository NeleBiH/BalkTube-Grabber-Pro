#!/bin/bash
# Build .deb package for BalkGrab
# Requires: dpkg-deb, python3, python3-venv
# Usage: ./build-deb.sh

set -e

APP_NAME="balkgrab"
APP_VERSION="0.3.0"
ARCH="amd64"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$SCRIPT_DIR/build/${APP_NAME}_${APP_VERSION}_${ARCH}"
OUTPUT_DIR="$SCRIPT_DIR/dist"

echo "=========================================="
echo "  Building .deb package"
echo "  ${APP_NAME} v${APP_VERSION}"
echo "=========================================="

# Check dependencies
if ! command -v dpkg-deb &>/dev/null; then
    echo "Error: dpkg-deb not found. Install with: sudo apt install dpkg"
    exit 1
fi

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$OUTPUT_DIR"

# Create directory structure
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/balkgrab"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/bin"

# Icons
for size in 16 32 48 64 128 256; do
    mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/${size}x${size}/apps"
    if [[ -f "$PROJECT_DIR/Icons/linux/icon_${size}x${size}.png" ]]; then
        cp "$PROJECT_DIR/Icons/linux/icon_${size}x${size}.png" \
           "$BUILD_DIR/usr/share/icons/hicolor/${size}x${size}/apps/balkgrab.png"
    fi
done

# Copy app files
cp "$PROJECT_DIR/BalkGrab.py" "$BUILD_DIR/opt/balkgrab/"
cp -r "$PROJECT_DIR/Icons" "$BUILD_DIR/opt/balkgrab/"
cp "$PROJECT_DIR/requirements.txt" "$BUILD_DIR/opt/balkgrab/"

# Create launcher script
cat > "$BUILD_DIR/usr/bin/balkgrab" << 'LAUNCHER'
#!/bin/bash
# BalkGrab launcher
INSTALL_DIR="/opt/balkgrab"

# Create venv on first run
if [[ ! -d "$INSTALL_DIR/.venv" ]]; then
    echo "First run: setting up Python environment..."
    python3 -m venv "$INSTALL_DIR/.venv"
    "$INSTALL_DIR/.venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"
    "$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade --pre yt-dlp
fi

exec "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/BalkGrab.py" "$@"
LAUNCHER
chmod +x "$BUILD_DIR/usr/bin/balkgrab"

# Desktop entry
cat > "$BUILD_DIR/usr/share/applications/balkgrab.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=BalkGrab
GenericName=YouTube Downloader
Comment=Download videos and music from YouTube
Exec=balkgrab
Icon=balkgrab
Terminal=false
Categories=AudioVideo;Audio;Video;Network;
Keywords=youtube;download;music;video;mp3;
StartupWMClass=balkgrab
EOF

# DEBIAN control file
cat > "$BUILD_DIR/DEBIAN/control" << EOF
Package: balkgrab
Version: ${APP_VERSION}
Section: multimedia
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.9), python3-venv, ffmpeg
Maintainer: NeleBiH <nele@balktube.dev>
Description: BalkGrab - YouTube Downloader
 Free & Open Source YouTube downloader with GUI.
 Search, preview, and download videos/audio from YouTube.
 Built with PySide6 and yt-dlp.
Homepage: https://github.com/NeleBiH/BalkGrab
EOF

# Post-install: create venv
cat > "$BUILD_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e
INSTALL_DIR="/opt/balkgrab"
if [[ ! -d "$INSTALL_DIR/.venv" ]]; then
    python3 -m venv "$INSTALL_DIR/.venv"
    "$INSTALL_DIR/.venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"
    "$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade --pre yt-dlp
fi
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
update-desktop-database /usr/share/applications 2>/dev/null || true
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# Post-remove: cleanup
cat > "$BUILD_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
if [[ "$1" = "purge" ]] || [[ "$1" = "remove" ]]; then
    rm -rf /opt/balkgrab/.venv
fi
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
update-desktop-database /usr/share/applications 2>/dev/null || true
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# Build .deb
DEB_FILE="$OUTPUT_DIR/${APP_NAME}_${APP_VERSION}_${ARCH}.deb"
dpkg-deb --build "$BUILD_DIR" "$DEB_FILE"

echo ""
echo "=========================================="
echo "  Build complete!"
echo "  Output: $DEB_FILE"
echo "=========================================="
echo ""
echo "  Install with: sudo dpkg -i $DEB_FILE"
echo "  Or:           sudo apt install ./$DEB_FILE"
