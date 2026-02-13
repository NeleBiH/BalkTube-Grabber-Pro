#!/bin/bash
# BalkGrab - Install / Update / Uninstall

APP_NAME="BalkGrab"
INSTALL_DIR="$HOME/.balkgrab"
DESKTOP_FILE="$HOME/.local/share/applications/balkgrab.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Old app names to clean up
OLD_INSTALL_DIRS=("$HOME/.balktube")
OLD_DESKTOP_FILES=(
    "$HOME/.local/share/applications/balktube.desktop"
)
OLD_ICON_NAMES=("balktube")
OLD_CONFIG_DIRS=(
    "$HOME/.config/BalkTube"
    "$HOME/.config/BalkTube Grabber Pro"
)

# ==========================================
# Functions
# ==========================================

show_menu() {
    echo ""
    echo "=========================================="
    echo "  $APP_NAME Setup"
    echo "=========================================="
    echo ""
    echo "  1) Install / Update"
    echo "  2) Uninstall"
    echo "  3) Exit"
    echo ""
    read -p "Choose an option [1-3]: " choice
    case "$choice" in
        1) do_install ;;
        2) do_uninstall ;;
        3) echo "Bye!"; exit 0 ;;
        *) echo "Invalid option."; show_menu ;;
    esac
}

cleanup_old_versions() {
    local found=false

    # Remove old install directories
    for dir in "${OLD_INSTALL_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            rm -rf "$dir"
            echo "  Cleaned up old install: $dir"
            found=true
        fi
    done

    # Remove old desktop entries
    for file in "${OLD_DESKTOP_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            rm -f "$file"
            echo "  Cleaned up old menu entry: $file"
            found=true
        fi
    done

    # Remove old icons
    for icon_name in "${OLD_ICON_NAMES[@]}"; do
        for size in 16 32 48 64 128 256; do
            local icon_file="$ICON_DIR/${size}x${size}/apps/${icon_name}.png"
            if [[ -f "$icon_file" ]]; then
                rm -f "$icon_file"
                found=true
            fi
        done
        if $found; then
            echo "  Cleaned up old icons: $icon_name"
        fi
    done

    # Remove old config directories
    for dir in "${OLD_CONFIG_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            rm -rf "$dir"
            echo "  Cleaned up old config: $dir"
            found=true
        fi
    done

    if $found; then
        echo ""
    fi
}

do_install() {
    echo ""
    echo "=========================================="
    echo "  Installing $APP_NAME"
    echo "=========================================="
    echo ""

    # Check source files
    if [[ ! -f "$SCRIPT_DIR/BalkGrab.py" ]]; then
        echo "Error: BalkGrab.py not found in $SCRIPT_DIR"
        echo "Please run this script from the project directory."
        exit 1
    fi

    # Clean up old versions first
    echo "[1/7] Cleaning up old versions..."
    cleanup_old_versions

    # Create install directory
    echo "[2/7] Creating install directory..."
    mkdir -p "$INSTALL_DIR"

    # Copy program files
    echo "[3/7] Copying program files..."
    cp "$SCRIPT_DIR/BalkGrab.py" "$INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/Icons" "$INSTALL_DIR/"

    # Create or reuse virtual environment
    echo "[4/7] Setting up Python environment..."
    if [[ ! -d "$INSTALL_DIR/.venv" ]]; then
        python3 -m venv "$INSTALL_DIR/.venv"
    fi

    # Install/update dependencies
    echo "[5/7] Installing dependencies..."
    "$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
    "$INSTALL_DIR/.venv/bin/pip" install --quiet PySide6 yt-dlp requests Pillow
    "$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade --pre yt-dlp

    # Install deno if not present
    if [[ ! -f "$HOME/.deno/bin/deno" ]]; then
        echo "[5.5/7] Installing deno (for YouTube signature solving)..."
        curl -fsSL https://deno.land/install.sh | sh > /dev/null 2>&1 || true
    fi

    # Install icons
    echo "[6/7] Installing icons..."
    for size in 16 32 48 64 128 256; do
        icon_dir="$ICON_DIR/${size}x${size}/apps"
        mkdir -p "$icon_dir"
        if [[ -f "$INSTALL_DIR/Icons/icon_${size}x${size}.png" ]]; then
            cp "$INSTALL_DIR/Icons/icon_${size}x${size}.png" "$icon_dir/balkgrab.png"
        fi
    done
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true

    # Create desktop entry
    echo "[7/7] Creating menu entry..."
    mkdir -p "$(dirname "$DESKTOP_FILE")"
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=BalkGrab
GenericName=YouTube Downloader
Comment=Download videos and music from YouTube
Exec=$INSTALL_DIR/.venv/bin/python "$INSTALL_DIR/BalkGrab.py"
Icon=balkgrab
Terminal=false
Categories=AudioVideo;Audio;Video;Network;
Keywords=youtube;download;music;video;mp3;
StartupWMClass=balkgrab
EOF
    chmod +x "$DESKTOP_FILE"
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

    echo ""
    echo "=========================================="
    echo "  Installation complete!"
    echo "=========================================="
    echo ""
    echo "  Installed to: $INSTALL_DIR"
    echo ""
    echo "  Find '$APP_NAME' in your application menu"
    echo "  Or run: $INSTALL_DIR/.venv/bin/python \"$INSTALL_DIR/BalkGrab.py\""
    echo ""
    echo "  To uninstall, run: ./setup.sh and choose option 2"
    echo ""
}

do_uninstall() {
    echo ""
    echo "=========================================="
    echo "  Uninstalling $APP_NAME"
    echo "=========================================="
    echo ""

    read -p "Are you sure? This will remove $APP_NAME and all old versions. [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        return
    fi

    # Remove current install
    echo "[1/4] Removing program files..."
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        echo "  Removed: $INSTALL_DIR"
    else
        echo "  Not found: $INSTALL_DIR (skipping)"
    fi

    # Remove icons
    echo "[2/4] Removing icons..."
    for size in 16 32 48 64 128 256; do
        icon_file="$ICON_DIR/${size}x${size}/apps/balkgrab.png"
        if [[ -f "$icon_file" ]]; then
            rm -f "$icon_file"
        fi
    done
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true

    # Remove desktop entry
    echo "[3/4] Removing menu entry..."
    if [[ -f "$DESKTOP_FILE" ]]; then
        rm -f "$DESKTOP_FILE"
        echo "  Removed: $DESKTOP_FILE"
    fi
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

    # Clean up ALL old versions
    echo "[4/4] Cleaning up old versions..."
    cleanup_old_versions

    # Remove current config
    if [[ -d "$HOME/.config/BalkGrab" ]]; then
        rm -rf "$HOME/.config/BalkGrab"
        echo "  Removed config: ~/.config/BalkGrab"
    fi

    echo ""
    echo "=========================================="
    echo "  Uninstall complete!"
    echo "=========================================="
    echo ""
    echo "  $APP_NAME has been fully removed from your system."
    echo ""
}

# ==========================================
# Main
# ==========================================
show_menu
