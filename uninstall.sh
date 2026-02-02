#!/bin/bash
# BalkTube Grabber Pro - Uninstall Script

APP_NAME="BalkTube Grabber Pro"
INSTALL_DIR="$HOME/.balktube"
DESKTOP_FILE="$HOME/.local/share/applications/balktube.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor"

echo "=========================================="
echo "  Uninstalling $APP_NAME"
echo "=========================================="

# Confirm uninstall
read -p "Are you sure you want to uninstall $APP_NAME? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

# Remove install directory
echo "[1/3] Removing program files..."
if [[ -d "$INSTALL_DIR" ]]; then
    rm -rf "$INSTALL_DIR"
    echo "  Removed: $INSTALL_DIR"
else
    echo "  Not found: $INSTALL_DIR (skipping)"
fi

# Remove icons
echo "[2/3] Removing icons..."
for size in 16 32 48 64 128 256; do
    icon_file="$ICON_DIR/${size}x${size}/apps/balktube.png"
    if [[ -f "$icon_file" ]]; then
        rm -f "$icon_file"
        echo "  Removed: $icon_file"
    fi
done

# Update icon cache
gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true

# Remove desktop entry
echo "[3/3] Removing menu entry..."
if [[ -f "$DESKTOP_FILE" ]]; then
    rm -f "$DESKTOP_FILE"
    echo "  Removed: $DESKTOP_FILE"
else
    echo "  Not found: $DESKTOP_FILE (skipping)"
fi

# Update desktop database
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo ""
echo "=========================================="
echo "  Uninstall complete!"
echo "=========================================="
echo ""
echo "$APP_NAME has been removed from your system."
echo ""
echo "Note: User settings in ~/.config/BalkTube were NOT removed."
echo "To remove settings too, run: rm -rf ~/.config/BalkTube"
echo ""
