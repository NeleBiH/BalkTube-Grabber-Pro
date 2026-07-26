#!/bin/bash
# ==========================================
#  BalkGrab - Setup Script
#  Install / Update / Uninstall
# ==========================================

APP_NAME="BalkGrab"
INSTALL_DIR="$HOME/.balkgrab"
CONFIG_DIR="$HOME/.config/BalkGrab"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/balkgrab.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$INSTALL_DIR/.venv"
LAUNCHER="$INSTALL_DIR/launcher.sh"

PY_PACKAGES="PySide6 yt-dlp requests"

# Old app names to clean up
OLD_INSTALL_DIRS=("$HOME/.balktube")
OLD_DESKTOP_FILES=(
    "$HOME/.local/share/applications/balktube.desktop"
    "$HOME/.local/share/applications/balktube-grabber.desktop"
)
OLD_ICON_NAMES=("balktube" "balktube-grabber")

# ==========================================
# Colors
# ==========================================
if [[ -t 1 ]] && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
    RED='\e[0;31m'; BRIGHT_RED='\e[1;31m'; GREEN='\e[1;32m'
    BRIGHT_GREEN='\e[1;92m'; YELLOW='\e[1;33m'; CYAN='\e[0;36m'
    BRIGHT_CYAN='\e[1;96m'; WHITE='\e[1;37m'; DIM='\e[2m'
    BOLD='\e[1m'; RESET='\e[0m'
else
    RED=''; BRIGHT_RED=''; GREEN=''; BRIGHT_GREEN=''; YELLOW=''
    CYAN=''; BRIGHT_CYAN=''; WHITE=''; DIM=''; BOLD=''; RESET=''
fi

print_step() { echo ""; echo -e "${BOLD}${WHITE}$1${RESET}"; }
print_ok()   { echo -e "  ${GREEN}✓ $1${RESET}"; }
print_info() { echo -e "  ${CYAN}→ $1${RESET}"; }
print_warn() { echo -e "  ${YELLOW}⚠ $1${RESET}"; }
print_err()  { echo -e "  ${BRIGHT_RED}✗ ERROR: $1${RESET}"; }

# ==========================================
# Version
# ==========================================
get_version() {
    local ver
    ver=$(grep -m1 'APP_VERSION\s*=' "$SCRIPT_DIR/__init__.py" 2>/dev/null \
          | grep -oP '"[^"]*"' | tr -d '"')
    echo "${ver:-0.4.0}"
}

# ==========================================
# Banner
# ==========================================
show_header() {
    local version; version=$(get_version)
    local ver_line; printf -v ver_line "%-41s" "v${version}"
    clear
    echo ""
    echo -e "${CYAN}  ╔═══════════════════════════════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${CYAN}  ║${RESET}                                                                  ${CYAN}                     ║${RESET}"
    echo -e "${CYAN}  ║${RESET}   ${BRIGHT_GREEN}  ██  ${RESET} ${BRIGHT_RED}█▄${RESET}      ${BRIGHT_GREEN}██████╗  █████╗ ██╗     ██╗  ██╗  ██████╗ ██████╗  █████╗ ██████╗${RESET} ${CYAN}   ║${RESET}"
    echo -e "${CYAN}  ║${RESET}   ${BRIGHT_GREEN}  ██   ${RESET}${BRIGHT_RED}████▄${RESET}   ${BRIGHT_GREEN}██╔══██╗██╔══██╗██║     ██║ ██╔╝ ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗${RESET}${CYAN}   ║${RESET}"
    echo -e "${CYAN}  ║${RESET}   ${BRIGHT_GREEN}  ██   ${RESET}${BRIGHT_RED}██████▌${RESET} ${BRIGHT_GREEN}██████╔╝███████║██║     █████╔╝  ██║  ███╗██████╔╝███████║██████╔╝${RESET}${CYAN}   ║${RESET}"
    echo -e "${CYAN}  ║${RESET}   ${BRIGHT_GREEN}██████ ${RESET}${BRIGHT_RED}██████▌${RESET} ${BRIGHT_GREEN}██╔══██╗██╔══██║██║     ██╔═██╗  ██║   ██║██╔══██╗██╔══██║██╔══██╗${RESET} ${CYAN}  ║${RESET}"
    echo -e "${CYAN}  ║${RESET}   ${BRIGHT_GREEN} ████  ${RESET}${BRIGHT_RED}████▀${RESET}   ${BRIGHT_GREEN}██████╔╝██║  ██║███████╗██║  ██╗ ╚██████╔╝██║  ██║██║  ██║██████╔╝${RESET} ${CYAN}  ║${RESET}"
    echo -e "${CYAN}  ║${RESET}   ${BRIGHT_GREEN}  ██  ${RESET} ${BRIGHT_RED}█▀${RESET}      ${BRIGHT_GREEN}╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝${RESET}  ${CYAN}   ║${RESET}"
    echo -e "${CYAN}  ║${RESET}             ${BRIGHT_GREEN}${RESET}                                                                      ${CYAN}    ║${RESET}"
    echo -e "${CYAN}  ║               ${RESET}          ${CYAN}Free & Open Source YouTube Downloader${RESET}           ${CYAN}              ║${RESET}"
    echo -e "${CYAN}  ║${RESET}                                     ${YELLOW}${ver_line}${RESET}${CYAN}         ║${RESET}"
    echo -e "${CYAN}  ╠═══════════════════════════════════════════════════════════════════════════════════════╣${RESET}"
    echo -e "${CYAN}  ║               ${RESET}       ${YELLOW}★${RESET}  ${BOLD}Welcome to the BalkGrab Setup Script${RESET}  ${YELLOW}★${RESET} ${CYAN}                      ║${RESET}"
    echo -e "${CYAN}  ╚═══════════════════════════════════════════════════════════════════════════════════════╝${RESET}"
    echo ""
}

# ==========================================
# Distro detection & system deps
# ==========================================
detect_pkg_manager() {
    if   command -v pacman    &>/dev/null; then echo "pacman"
    elif command -v apt-get   &>/dev/null; then echo "apt"
    elif command -v dnf       &>/dev/null; then echo "dnf"
    elif command -v yum       &>/dev/null; then echo "yum"
    elif command -v zypper    &>/dev/null; then echo "zypper"
    elif command -v xbps-install &>/dev/null; then echo "xbps"
    elif command -v emerge    &>/dev/null; then echo "emerge"
    elif command -v apk       &>/dev/null; then echo "apk"
    else echo "unknown"
    fi
}

install_system_deps() {
    local pkg_mgr; pkg_mgr=$(detect_pkg_manager)
    print_info "Package manager: ${BOLD}$pkg_mgr${RESET}"

    # Check what's missing
    local need_python=false need_pip=false need_ffmpeg=false need_venv=false

    command -v python3 &>/dev/null || need_python=true
    command -v ffmpeg  &>/dev/null || need_ffmpeg=true

    if ! $need_python; then
        python3 -m pip --version &>/dev/null || need_pip=true
        python3 -m venv --help   &>/dev/null || need_venv=true
    fi

    if ! $need_python && ! $need_pip && ! $need_venv && ! $need_ffmpeg; then
        print_ok "All system dependencies present"
        return 0
    fi

    print_info "Installing missing system dependencies..."

    case "$pkg_mgr" in
        pacman)
            local pkgs=()
            $need_python  && pkgs+=("python")
            $need_ffmpeg  && pkgs+=("ffmpeg")
            # pacman's python includes pip and venv
            [[ ${#pkgs[@]} -gt 0 ]] && sudo pacman -S --needed --noconfirm "${pkgs[@]}"
            ;;
        apt)
            local pkgs=()
            $need_python  && pkgs+=("python3")
            $need_pip     && pkgs+=("python3-pip")
            $need_venv    && pkgs+=("python3-venv")
            $need_ffmpeg  && pkgs+=("ffmpeg")
            if [[ ${#pkgs[@]} -gt 0 ]]; then
                sudo apt-get update -qq
                sudo apt-get install -y "${pkgs[@]}"
            fi
            ;;
        dnf)
            local pkgs=()
            $need_python  && pkgs+=("python3")
            $need_pip     && pkgs+=("python3-pip")
            $need_ffmpeg  && pkgs+=("ffmpeg")
            [[ ${#pkgs[@]} -gt 0 ]] && sudo dnf install -y "${pkgs[@]}"
            ;;
        yum)
            local pkgs=()
            $need_python  && pkgs+=("python3")
            $need_pip     && pkgs+=("python3-pip")
            $need_ffmpeg  && pkgs+=("ffmpeg")
            [[ ${#pkgs[@]} -gt 0 ]] && sudo yum install -y "${pkgs[@]}"
            ;;
        zypper)
            local pkgs=()
            $need_python  && pkgs+=("python3")
            $need_pip     && pkgs+=("python3-pip")
            $need_ffmpeg  && pkgs+=("ffmpeg")
            [[ ${#pkgs[@]} -gt 0 ]] && sudo zypper install -y "${pkgs[@]}"
            ;;
        xbps)
            local pkgs=()
            $need_python  && pkgs+=("python3")
            $need_ffmpeg  && pkgs+=("ffmpeg")
            [[ ${#pkgs[@]} -gt 0 ]] && sudo xbps-install -Sy "${pkgs[@]}"
            ;;
        emerge)
            $need_python  && sudo emerge dev-lang/python
            $need_ffmpeg  && sudo emerge media-video/ffmpeg
            ;;
        apk)
            local pkgs=()
            $need_python  && pkgs+=("python3")
            $need_pip     && pkgs+=("py3-pip")
            $need_ffmpeg  && pkgs+=("ffmpeg")
            [[ ${#pkgs[@]} -gt 0 ]] && sudo apk add "${pkgs[@]}"
            ;;
        *)
            print_warn "Unknown package manager — install manually: python3 python3-pip ffmpeg"
            ;;
    esac

    # Verify after install
    if ! command -v python3 &>/dev/null; then
        print_err "python3 not found after install. Please install it manually."
        exit 1
    fi
    if ! command -v ffmpeg &>/dev/null; then
        print_warn "ffmpeg not found — audio conversion will not work."
        print_warn "Install it via your package manager: ffmpeg"
    fi

    print_ok "System dependencies ready"

    install_deno
}

# ==========================================
# Python venv + pip packages
# ==========================================
setup_venv() {
    local is_update="${1:-false}"

    if [[ "$is_update" == "true" ]] && [[ -d "$VENV_DIR" ]]; then
        print_info "Upgrading Python packages..."
        "$VENV_DIR/bin/pip" install --upgrade --quiet $PY_PACKAGES
        print_ok "Packages upgraded"
    else
        print_info "Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_ok "venv created"

        print_info "Installing Python packages (this may take a moment)..."
        "$VENV_DIR/bin/pip" install --upgrade --quiet pip
        "$VENV_DIR/bin/pip" install --quiet $PY_PACKAGES
        print_ok "Packages installed: $PY_PACKAGES"
    fi
}

# ==========================================
# Icons
# ==========================================
install_icons() {
    local icons_source="$1"
    local installed=0
    for size in 16 32 48 64 128 256; do
        local icon_dir="$ICON_DIR/${size}x${size}/apps"
        mkdir -p "$icon_dir"
        if [[ -f "$icons_source/icon_${size}x${size}.png" ]]; then
            cp "$icons_source/icon_${size}x${size}.png" "$icon_dir/balkgrab.png"
            (( installed++ )) || true
        fi
    done
    if [[ $installed -eq 0 ]]; then
        print_warn "No icon files found in: $icons_source"
        return
    fi
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
    command -v kbuildsycoca5 &>/dev/null && kbuildsycoca5 --noincremental 2>/dev/null || true
    command -v kbuildsycoca6 &>/dev/null && kbuildsycoca6 --noincremental 2>/dev/null || true
    xdg-icon-resource forceupdate 2>/dev/null || true
}

remove_icons() {
    for size in 16 32 48 64 128 256; do
        rm -f "$ICON_DIR/${size}x${size}/apps/balkgrab.png"
    done
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
    command -v kbuildsycoca5 &>/dev/null && kbuildsycoca5 --noincremental 2>/dev/null || true
    command -v kbuildsycoca6 &>/dev/null && kbuildsycoca6 --noincremental 2>/dev/null || true
    xdg-icon-resource forceupdate 2>/dev/null || true
}

# ==========================================
# Launcher script
# ==========================================
create_launcher() {
    cat > "$LAUNCHER" << EOF
#!/bin/bash
export PATH="\$HOME/.deno/bin:\$PATH"
export PYTHONPATH="$INSTALL_DIR"
exec "$VENV_DIR/bin/python" -m balkgrab "\$@"
EOF
    chmod +x "$LAUNCHER"

    mkdir -p "$HOME/.local/bin"
    ln -sf "$LAUNCHER" "$HOME/.local/bin/balkgrab"
}

# ==========================================
# Desktop entry
# ==========================================
create_desktop_entry() {
    mkdir -p "$DESKTOP_DIR"
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=BalkGrab
GenericName=YouTube Downloader
Comment=Download videos and music from YouTube
Exec=$LAUNCHER
Icon=balkgrab
Terminal=false
Categories=AudioVideo;Audio;Video;Network;
Keywords=youtube;download;music;video;mp3;
StartupWMClass=balkgrab
EOF
    chmod +x "$DESKTOP_FILE"
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    command -v kbuildsycoca5 &>/dev/null && kbuildsycoca5 --noincremental 2>/dev/null || true
    command -v kbuildsycoca6 &>/dev/null && kbuildsycoca6 --noincremental 2>/dev/null || true
}

# ==========================================
# Deno (yt-dlp signature solving)
# ==========================================
install_deno() {
    if command -v deno &>/dev/null || [[ -f "$HOME/.deno/bin/deno" ]]; then
        print_ok "deno already installed"
        return
    fi

    local pkg_mgr; pkg_mgr=$(detect_pkg_manager)
    local installed=false

    print_info "Installing deno (needed for YouTube downloads)..."

    case "$pkg_mgr" in
        pacman)
            sudo pacman -S --needed --noconfirm deno && installed=true
            ;;
        dnf)
            sudo dnf install -y deno && installed=true
            ;;
        zypper)
            sudo zypper install -y deno && installed=true
            ;;
    esac

    if ! $installed; then
        if command -v curl &>/dev/null; then
            print_info "deno not in repos, installing via curl..."
            curl -fsSL https://deno.land/install.sh | sh > /dev/null 2>&1 && installed=true
        fi
    fi

    if $installed && (command -v deno &>/dev/null || [[ -f "$HOME/.deno/bin/deno" ]]); then
        print_ok "deno installed"
    else
        print_warn "deno install failed — install manually: https://deno.land"
    fi
}

# ==========================================
# Cleanup old versions
# ==========================================
cleanup_old_versions() {
    local found=false
    for dir in "${OLD_INSTALL_DIRS[@]}"; do
        [[ -d "$dir" ]] && rm -rf "$dir" && echo -e "  ${DIM}Cleaned: $dir${RESET}" && found=true
    done
    for file in "${OLD_DESKTOP_FILES[@]}"; do
        [[ -f "$file" ]] && rm -f "$file" && echo -e "  ${DIM}Cleaned: $(basename "$file")${RESET}" && found=true
    done
    for icon_name in "${OLD_ICON_NAMES[@]}"; do
        for size in 16 32 48 64 128 256; do
            local f="$ICON_DIR/${size}x${size}/apps/${icon_name}.png"
            [[ -f "$f" ]] && rm -f "$f" && found=true
        done
    done
    # Remove old AppImage if present (no longer needed)
    if [[ -f "$INSTALL_DIR/BalkGrab.AppImage" ]]; then
        rm -f "$INSTALL_DIR/BalkGrab.AppImage"
        echo -e "  ${DIM}Removed old AppImage${RESET}"
        found=true
    fi
    # Remove old single-file install (replaced by balkgrab/ package)
    if [[ -f "$INSTALL_DIR/BalkGrab.py" ]]; then
        rm -f "$INSTALL_DIR/BalkGrab.py"
        echo -e "  ${DIM}Removed old BalkGrab.py${RESET}"
        found=true
    fi
    # Remove old launcher at conflicting path (now launcher.sh)
    # Only remove if it's a file (old launcher), not the balkgrab/ package directory
    if [[ -f "$INSTALL_DIR/balkgrab" ]]; then
        rm -f "$INSTALL_DIR/balkgrab"
        echo -e "  ${DIM}Removed old launcher${RESET}"
        found=true
    fi
    # Remove broken symlink from previous versions
    if [[ -L "$HOME/.local/bin/balkgrab" ]]; then
        rm -f "$HOME/.local/bin/balkgrab"
        echo -e "  ${DIM}Removed broken symlink${RESET}"
        found=true
    fi
    $found && echo -e "  ${DIM}Old files cleaned up${RESET}" || true
}

# ==========================================
# Install / Update
# ==========================================
do_install() {
    local is_update=false
    [[ -d "$INSTALL_DIR/balkgrab" ]] && is_update=true

    echo ""
    if $is_update; then
        echo -e "${BOLD}${WHITE}  ══════════════════════════════════════${RESET}"
        echo -e "${BOLD}${WHITE}    Updating ${GREEN}${APP_NAME}${RESET}"
        echo -e "${BOLD}${WHITE}  ══════════════════════════════════════${RESET}"
    else
        echo -e "${BOLD}${WHITE}  ══════════════════════════════════════${RESET}"
        echo -e "${BOLD}${WHITE}    Installing ${GREEN}${APP_NAME}${RESET}"
        echo -e "${BOLD}${WHITE}  ══════════════════════════════════════${RESET}"
    fi
    echo ""

    # Provjeri postoji li __init__.py u script diru (balkgrab paket)
    if [[ ! -f "$SCRIPT_DIR/__init__.py" ]]; then
        print_err "balkgrab package not found in $SCRIPT_DIR"
        exit 1
    fi

    # ---- UPDATE: kopiraj .py, osvježi launcher/ikone/desktop, upgradeaj pakete ----
    if $is_update; then
        print_step "[1/4] Cleaning up old files..."
        cleanup_old_versions
        print_ok "Done"

        print_step "[2/4] Copying balkgrab package + launcher..."
        rm -rf "$INSTALL_DIR/balkgrab"
        cp -r "$SCRIPT_DIR" "$INSTALL_DIR/balkgrab"
        rm -f "$INSTALL_DIR/balkgrab/setup_BalkGrab.sh"
        rm -rf "$INSTALL_DIR/balkgrab/__pycache__"
        if [[ ! -f "$INSTALL_DIR/balkgrab/__init__.py" ]]; then
            print_err "Failed to copy balkgrab package"
            exit 1
        fi
        create_launcher
        print_ok "BalkGrab updated ($(get_version))"

        print_step "[3/4] Updating icons and menu entry..."
        if [[ -d "$SCRIPT_DIR/Icons/linux" ]]; then
            install_icons "$SCRIPT_DIR/Icons/linux"
            print_ok "Icons updated"
        fi
        create_desktop_entry
        print_ok "Menu entry updated"

        print_step "[4/4] Upgrading Python packages..."
        setup_venv "true"

        install_deno

        echo ""
        echo -e "${CYAN}  ══════════════════════════════════════${RESET}"
        echo -e "${GREEN}${BOLD}    ✓ Update complete!${RESET}"
        echo -e "${CYAN}  ══════════════════════════════════════${RESET}"
        echo ""
        echo -e "  ${BOLD}Version:${RESET} $(get_version)"
        echo -e "  ${DIM}Settings and download history untouched${RESET}"
        echo ""
        return
    fi

    # ---- FRESH INSTALL ----
    print_step "[1/5] Cleaning up old versions..."
    cleanup_old_versions
    print_ok "Done"

    print_step "[2/5] Installing system dependencies..."
    install_system_deps

    print_step "[3/5] Setting up Python environment..."
    mkdir -p "$INSTALL_DIR"
    rm -rf "$INSTALL_DIR/balkgrab"
    cp -r "$SCRIPT_DIR" "$INSTALL_DIR/balkgrab"
    rm -f "$INSTALL_DIR/balkgrab/setup_BalkGrab.sh"
    rm -rf "$INSTALL_DIR/balkgrab/__pycache__"
    if [[ ! -f "$INSTALL_DIR/balkgrab/__init__.py" ]]; then
        print_err "Failed to copy balkgrab package"
        exit 1
    fi
    print_ok "BalkGrab package copied"
    setup_venv "false"
    create_launcher
    print_ok "Launcher created: $LAUNCHER"

    print_step "[4/5] Installing icons..."
    if [[ -d "$SCRIPT_DIR/Icons/linux" ]]; then
        install_icons "$SCRIPT_DIR/Icons/linux"
        print_ok "Icons installed"
    fi

    print_step "[5/5] Creating menu entry..."
    create_desktop_entry
    print_ok "Menu entry created"

    echo ""
    echo -e "${CYAN}  ══════════════════════════════════════${RESET}"
    echo -e "${GREEN}${BOLD}    ✓ Installation complete!${RESET}"
    echo -e "${CYAN}  ══════════════════════════════════════${RESET}"
    echo ""
    echo -e "  ${BOLD}Installed to:${RESET} $INSTALL_DIR"
    echo -e "  Find ${WHITE}${BOLD}$APP_NAME${RESET} in your application menu"
    echo ""
    echo -e "  ${DIM}Or run directly: $LAUNCHER${RESET}"
    echo -e "  ${DIM}To uninstall: ./$(basename "$0") → option 2${RESET}"
    echo ""
}

# ==========================================
# Uninstall
# ==========================================
do_uninstall() {
    echo ""
    echo -e "${BOLD}${WHITE}  ══════════════════════════════════════${RESET}"
    echo -e "${BOLD}${WHITE}    Uninstalling ${RED}${APP_NAME}${RESET}"
    echo -e "${BOLD}${WHITE}  ══════════════════════════════════════${RESET}"
    echo ""
    echo -e "  ${YELLOW}This will remove $APP_NAME and all associated files.${RESET}"
    echo ""
    read -p "  Are you sure? [y/N] " -n 1 -r; echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "  ${DIM}Cancelled.${RESET}"; echo ""; return
    fi

    print_step "[1/4] Removing program..."
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        print_ok "Removed: $INSTALL_DIR"
    else
        print_info "Not installed — skipping"
    fi
    rm -f "$HOME/.local/bin/balkgrab"

    print_step "[2/4] Removing icons..."
    remove_icons
    print_ok "Icons removed"

    print_step "[3/4] Removing menu entry..."
    if [[ -f "$DESKTOP_FILE" ]]; then
        rm -f "$DESKTOP_FILE"
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
        print_ok "Menu entry removed"
    else
        print_info "No menu entry found — skipping"
    fi

    print_step "[4/4] Cleaning up old versions..."
    cleanup_old_versions
    print_ok "Done"

    # Ask about config/history
    if [[ -d "$CONFIG_DIR" ]]; then
        echo ""
        echo -e "  ${CYAN}User data found at $CONFIG_DIR${RESET}"
        echo -e "  ${DIM}(settings + download history)${RESET}"
        read -p "  Remove user data too? [y/N] " -n 1 -r; echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$CONFIG_DIR"
            print_ok "User data removed"
        else
            print_info "User data kept at $CONFIG_DIR"
        fi
    fi

    echo ""
    echo -e "${CYAN}  ══════════════════════════════════════${RESET}"
    echo -e "${GREEN}${BOLD}    ✓ Uninstall complete!${RESET}"
    echo -e "${CYAN}  ══════════════════════════════════════${RESET}"
    echo ""
}

# ==========================================
# Main Menu
# ==========================================
show_header

echo -e "  ${BOLD}What would you like to do?${RESET}"
echo ""
echo -e "  ${GREEN}${BOLD}[1]${RESET}  Install / Update"
echo -e "  ${RED}${BOLD}[2]${RESET}  Uninstall"
echo -e "  ${DIM}[3]  Exit${RESET}"
echo ""
read -p "  Choose [1-3]: " choice
echo ""

case "$choice" in
    1) do_install ;;
    2) do_uninstall ;;
    3) echo -e "  ${DIM}Bye!${RESET}"; echo ""; exit 0 ;;
    *) echo -e "  ${YELLOW}⚠ Invalid option.${RESET}"; echo ""; exit 1 ;;
esac
