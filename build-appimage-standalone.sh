#!/bin/bash
# BalkTube Grabber Pro - Standalone AppImage Build Script
# Creates a FULLY PORTABLE AppImage with Python and all dependencies bundled

set -e

APP_NAME="BalkTube_Grabber_Pro"
APP_VERSION="0.1.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build-standalone"
APPDIR="$BUILD_DIR/$APP_NAME.AppDir"
ARCH=$(uname -m)

echo "=========================================="
echo "  Building Standalone $APP_NAME AppImage"
echo "  (with bundled Python + all dependencies)"
echo "=========================================="
echo ""

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Download standalone Python
echo "[1/7] Downloading portable Python..."
PYTHON_TAR="python-standalone.tar.gz"
wget -q --show-progress "https://github.com/indygreg/python-build-standalone/releases/download/20241016/cpython-3.11.10+20241016-${ARCH}-unknown-linux-gnu-install_only.tar.gz" -O "$PYTHON_TAR"

echo "[2/7] Extracting Python..."
mkdir -p "$APPDIR"
tar -xzf "$PYTHON_TAR" -C "$APPDIR"
# The archive extracts to 'python' directory
mv "$APPDIR/python/"* "$APPDIR/"
rmdir "$APPDIR/python"

# Verify Python works
echo "[3/7] Verifying Python installation..."
"$APPDIR/bin/python3" --version

# Install dependencies
echo "[4/7] Installing Python dependencies (PySide6, yt-dlp)..."
echo "      This may take several minutes..."
"$APPDIR/bin/python3" -m pip install --upgrade pip --quiet
"$APPDIR/bin/python3" -m pip install PySide6 yt-dlp requests --quiet
"$APPDIR/bin/python3" -m pip install --upgrade --pre yt-dlp --quiet

# Copy application
echo "[5/7] Copying application files..."
mkdir -p "$APPDIR/app"
cp "$SCRIPT_DIR/BalkTube Grabber Pro.py" "$APPDIR/app/"
cp -r "$SCRIPT_DIR/Icons" "$APPDIR/app/"

# Setup icons and desktop file
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/applications"
cp "$SCRIPT_DIR/Icons/icon_256x256.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/balktube.png"
cp "$SCRIPT_DIR/Icons/icon_256x256.png" "$APPDIR/balktube.png"
ln -sf balktube.png "$APPDIR/.DirIcon"

cat > "$APPDIR/balktube.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=BalkTube Grabber Pro
GenericName=YouTube Downloader
Comment=Download videos and music from YouTube
Exec=AppRun
Icon=balktube
Terminal=false
Categories=AudioVideo;Audio;Video;Network;
Keywords=youtube;download;music;video;mp3;
EOF
cp "$APPDIR/balktube.desktop" "$APPDIR/usr/share/applications/"

# Create AppRun
echo "[6/7] Creating AppRun launcher..."
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}

# Add deno to PATH if available (for yt-dlp)
if [[ -d "$HOME/.deno/bin" ]]; then
    export PATH="$HOME/.deno/bin:$PATH"
fi

# Set Python environment
export PATH="$HERE/bin:$PATH"
export PYTHONHOME="$HERE"
export PYTHONDONTWRITEBYTECODE=1

# PySide6/Qt environment
export QT_PLUGIN_PATH="$HERE/lib/python3.11/site-packages/PySide6/Qt/plugins"
export QML2_IMPORT_PATH="$HERE/lib/python3.11/site-packages/PySide6/Qt/qml"
export QT_QPA_PLATFORM_PLUGIN_PATH="$HERE/lib/python3.11/site-packages/PySide6/Qt/plugins/platforms"

# Multimedia backend
export QT_MEDIA_BACKEND="ffmpeg"

# Run the application
exec "$HERE/bin/python3" "$HERE/app/BalkTube Grabber Pro.py" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# Build AppImage
echo "[7/7] Building AppImage..."
APPIMAGETOOL="$BUILD_DIR/appimagetool"
wget -q --show-progress "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage" -O "$APPIMAGETOOL"
chmod +x "$APPIMAGETOOL"

# Extract appimagetool (FUSE might not be available)
"$APPIMAGETOOL" --appimage-extract > /dev/null 2>&1

OUTPUT_NAME="${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"

ARCH=$ARCH ./squashfs-root/AppRun "$APPDIR" "$OUTPUT_NAME" 2>&1 | grep -v "^WARNING"

# Move to project root
mv "$OUTPUT_NAME" "$SCRIPT_DIR/"

# Get final size
SIZE=$(du -h "$SCRIPT_DIR/$OUTPUT_NAME" | cut -f1)

echo ""
echo "=========================================="
echo "  Standalone AppImage built successfully!"
echo "=========================================="
echo ""
echo "Output: $SCRIPT_DIR/$OUTPUT_NAME"
echo "Size:   $SIZE"
echo ""
echo "This AppImage is FULLY PORTABLE!"
echo "No Python, PySide6, or yt-dlp installation needed."
echo ""
echo "To run:"
echo "  chmod +x $OUTPUT_NAME"
echo "  ./$OUTPUT_NAME"
echo ""

# Cleanup
rm -rf "$BUILD_DIR"
echo "Build directory cleaned."
