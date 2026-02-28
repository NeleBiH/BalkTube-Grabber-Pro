#!/bin/bash
# Build AppImage for BalkGrab
# Requires: wget (for appimagetool download)
# Usage: ./build-appimage.sh

set -e

APP_NAME="BalkGrab"
APP_VERSION="0.3.0"
ARCH="x86_64"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$SCRIPT_DIR/build/appimage"
APPDIR="$BUILD_DIR/${APP_NAME}.AppDir"
OUTPUT_DIR="$SCRIPT_DIR/dist"
APPIMAGETOOL="$SCRIPT_DIR/build/appimagetool-${ARCH}.AppImage"

echo "=========================================="
echo "  Building AppImage"
echo "  ${APP_NAME} v${APP_VERSION}"
echo "=========================================="

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$APPDIR"

# Download appimagetool if needed
if [[ ! -f "$APPIMAGETOOL" ]]; then
    echo "[1/5] Downloading appimagetool..."
    mkdir -p "$(dirname "$APPIMAGETOOL")"
    wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage" \
         -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
else
    echo "[1/5] appimagetool already present"
fi

# Create AppDir structure
echo "[2/5] Creating AppDir structure..."
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/opt/balkgrab"

# Copy app files
cp "$PROJECT_DIR/BalkGrab.py" "$APPDIR/opt/balkgrab/"
cp "$PROJECT_DIR/requirements.txt" "$APPDIR/opt/balkgrab/"
cp -r "$PROJECT_DIR/Icons" "$APPDIR/opt/balkgrab/"

# Icons
for size in 16 32 48 64 128 256; do
    mkdir -p "$APPDIR/usr/share/icons/hicolor/${size}x${size}/apps"
    if [[ -f "$PROJECT_DIR/Icons/linux/icon_${size}x${size}.png" ]]; then
        cp "$PROJECT_DIR/Icons/linux/icon_${size}x${size}.png" \
           "$APPDIR/usr/share/icons/hicolor/${size}x${size}/apps/balkgrab.png"
    fi
done

# Root icon (required by AppImage)
cp "$PROJECT_DIR/Icons/linux/icon_256x256.png" "$APPDIR/balkgrab.png"

# Create embedded venv with all dependencies
echo "[3/5] Creating Python environment (this may take a minute)..."
python3 -m venv "$APPDIR/opt/balkgrab/.venv"
"$APPDIR/opt/balkgrab/.venv/bin/pip" install --quiet --upgrade pip
"$APPDIR/opt/balkgrab/.venv/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"
"$APPDIR/opt/balkgrab/.venv/bin/pip" install --quiet --upgrade --pre yt-dlp

# AppRun script
echo "[4/5] Creating AppRun..."
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "$0")")"
export PATH="$APPDIR/opt/balkgrab/.venv/bin:$PATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
exec "$APPDIR/opt/balkgrab/.venv/bin/python" "$APPDIR/opt/balkgrab/BalkGrab.py" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# Desktop entry
cat > "$APPDIR/balkgrab.desktop" << EOF
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

# Also copy to standard location
cp "$APPDIR/balkgrab.desktop" "$APPDIR/usr/share/applications/"

# Build AppImage
echo "[5/5] Building AppImage..."
ARCH=$ARCH "$APPIMAGETOOL" "$APPDIR" "$OUTPUT_DIR/${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"

echo ""
echo "=========================================="
echo "  Build complete!"
echo "  Output: $OUTPUT_DIR/${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"
echo "=========================================="
echo ""
echo "  Run with: chmod +x ${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage && ./${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"
