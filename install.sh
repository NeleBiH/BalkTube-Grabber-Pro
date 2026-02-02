#!/bin/bash
# BalkTube Grabber Pro - Install Script

set -e

APP_NAME="BalkTube Grabber Pro"
INSTALL_DIR="$HOME/.balktube"
DESKTOP_FILE="$HOME/.local/share/applications/balktube.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor"

echo "=========================================="
echo "  Installing $APP_NAME"
echo "=========================================="

# Get the directory where install.sh is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running from project directory
if [[ ! -f "$SCRIPT_DIR/BalkTube Grabber Pro.py" ]]; then
    echo "Error: BalkTube Grabber Pro.py not found in $SCRIPT_DIR"
    echo "Please run this script from the project directory."
    exit 1
fi

# Create install directory
echo "[1/6] Creating install directory..."
mkdir -p "$INSTALL_DIR"

# Copy program files
echo "[2/6] Copying program files..."
cp "$SCRIPT_DIR/BalkTube Grabber Pro.py" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/Icons" "$INSTALL_DIR/"

# Create virtual environment if it doesn't exist
echo "[3/6] Setting up Python environment..."
if [[ ! -d "$INSTALL_DIR/.venv" ]]; then
    python3 -m venv "$INSTALL_DIR/.venv"
fi

# Install dependencies
echo "[4/6] Installing dependencies..."
"$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install --quiet PySide6 yt-dlp requests Pillow

# Upgrade yt-dlp to latest dev version
"$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade --pre yt-dlp

# Install deno if not present
if [[ ! -f "$HOME/.deno/bin/deno" ]]; then
    echo "[4.5/6] Installing deno (for YouTube signature solving)..."
    curl -fsSL https://deno.land/install.sh | sh > /dev/null 2>&1 || true
fi

# Install icons to system
echo "[5/6] Installing icons..."
for size in 16 32 48 64 128 256; do
    icon_dir="$ICON_DIR/${size}x${size}/apps"
    mkdir -p "$icon_dir"
    if [[ -f "$INSTALL_DIR/Icons/icon_${size}x${size}.png" ]]; then
        cp "$INSTALL_DIR/Icons/icon_${size}x${size}.png" "$icon_dir/balktube.png"
    fi
done

# Update icon cache
gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true

# Create desktop entry
echo "[6/6] Creating menu entry..."
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=BalkTube Grabber Pro
GenericName=YouTube Downloader
Comment=Download videos and music from YouTube
Exec=$INSTALL_DIR/.venv/bin/python "$INSTALL_DIR/BalkTube Grabber Pro.py"
Icon=balktube
Terminal=false
Categories=AudioVideo;Audio;Video;Network;
Keywords=youtube;download;music;video;mp3;
StartupWMClass=balktube
EOF

# Make desktop file executable
chmod +x "$DESKTOP_FILE"

# Update desktop database
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo ""
echo "=========================================="
echo "  Installation complete!"
echo "=========================================="
echo ""
echo "Installed to: $INSTALL_DIR"
echo ""
echo "You can now:"
echo "  - Find '$APP_NAME' in your application menu"
echo "  - Run from terminal: $INSTALL_DIR/.venv/bin/python \"$INSTALL_DIR/BalkTube Grabber Pro.py\""
echo ""
echo "To uninstall, run: ./uninstall.sh"
echo ""
