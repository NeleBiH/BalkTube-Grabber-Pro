#!/bin/bash
# BalkTube Grabber - Fedora/RHEL/openSUSE .rpm Package Builder
# NOT TESTED - nemam na cemu da testiram dok ne odradim install Fedore

set -e

APP_NAME="balktube-grabber"
APP_VERSION="0.1.2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RPMBUILD_DIR="/tmp/balktube-rpmbuild"

echo "=========================================="
echo "  Building ${APP_NAME} .rpm package"
echo "=========================================="
echo ""

# Check rpmbuild
if ! command -v rpmbuild &>/dev/null; then
    echo "ERROR: rpmbuild not found!"
    echo "Install with: sudo dnf install rpm-build    (on Fedora)"
    echo "         or:  sudo pacman -S rpm-tools       (on Arch)"
    exit 1
fi

# Clean previous build
rm -rf "$RPMBUILD_DIR"

echo "[1/4] Creating RPM build structure..."
mkdir -p "$RPMBUILD_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

echo "[2/4] Creating source tarball..."
TARBALL_DIR="${APP_NAME}-${APP_VERSION}"
mkdir -p "/tmp/$TARBALL_DIR/Icons"
cp "$SCRIPT_DIR/BalkTube Grabber.py" "/tmp/$TARBALL_DIR/"
cp "$SCRIPT_DIR/Icons/"*.png "/tmp/$TARBALL_DIR/Icons/"
cp "$SCRIPT_DIR/Icons/icon.ico" "/tmp/$TARBALL_DIR/Icons/" 2>/dev/null || true
cp "$SCRIPT_DIR/LICENSE" "/tmp/$TARBALL_DIR/" 2>/dev/null || true

tar czf "$RPMBUILD_DIR/SOURCES/${TARBALL_DIR}.tar.gz" -C /tmp "$TARBALL_DIR"
rm -rf "/tmp/$TARBALL_DIR"

echo "[3/4] Creating spec file..."
cat > "$RPMBUILD_DIR/SPECS/${APP_NAME}.spec" << 'SPEC'
Name:           balktube-grabber
Version:        0.1.2
Release:        1%{?dist}
Summary:        YouTube downloader with GUI - ClipGrab alternative
License:        MIT
URL:            https://github.com/NeleBiH/BalkTube-Grabber
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel

Requires:       python3 >= 3.9
Requires:       python3-pyside6
Requires:       python3-requests
Requires:       yt-dlp
Requires:       ffmpeg-free

Recommends:     deno

%description
BalkTube Grabber is a free, open-source YouTube downloader
inspired by ClipGrab. Download videos in various resolutions or
convert them to audio formats like MP3, FLAC, and more.

Features:
- Search YouTube directly from the app
- Preview videos before downloading
- Download videos from 240p to 4K
- Convert to audio: MP3, AAC, FLAC, WAV, OGG
- Download manager with progress tracking
- Built-in media player
- Multi-language support (EN/DE/HR)
- System tray integration

%prep
%setup -q

%install
rm -rf %{buildroot}

# Application files
mkdir -p "%{buildroot}/usr/share/%{name}"
mkdir -p "%{buildroot}/usr/share/%{name}/Icons"
cp "BalkTube Grabber.py" "%{buildroot}/usr/share/%{name}/"
cp Icons/*.png "%{buildroot}/usr/share/%{name}/Icons/"
cp Icons/icon.ico "%{buildroot}/usr/share/%{name}/Icons/" 2>/dev/null || true
cp LICENSE "%{buildroot}/usr/share/%{name}/" 2>/dev/null || true

# Launcher
mkdir -p "%{buildroot}/usr/bin"
cat > "%{buildroot}/usr/bin/%{name}" << 'LAUNCHER'
#!/bin/bash
exec python3 /usr/share/balktube-grabber/BalkTube\ Grabber\ Pro.py "$@"
LAUNCHER
chmod 755 "%{buildroot}/usr/bin/%{name}"

# Desktop entry
mkdir -p "%{buildroot}/usr/share/applications"
cat > "%{buildroot}/usr/share/applications/%{name}.desktop" << 'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=BalkTube Grabber
GenericName=YouTube Downloader
Comment=Download videos and music from YouTube
Exec=balktube-grabber
Icon=balktube-grabber
Terminal=false
Categories=AudioVideo;Audio;Video;Network;
Keywords=youtube;download;music;video;mp3;
StartupWMClass=balktube
DESKTOP

# Icons
for size in 16 32 64 128 256; do
    icon_dir="%{buildroot}/usr/share/icons/hicolor/${size}x${size}/apps"
    mkdir -p "$icon_dir"
    if [ -f "Icons/icon_${size}x${size}.png" ]; then
        cp "Icons/icon_${size}x${size}.png" "$icon_dir/%{name}.png"
    fi
done

%files
/usr/bin/%{name}
/usr/share/%{name}/
/usr/share/applications/%{name}.desktop
/usr/share/icons/hicolor/*/apps/%{name}.png

%post
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
update-desktop-database /usr/share/applications 2>/dev/null || true

%postun
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
update-desktop-database /usr/share/applications 2>/dev/null || true

%changelog
* Tue Feb 11 2025 BalkTube Team <nele@balktube.dev> - 0.1.2-1
- Fix bare except clauses
- Fix QMediaPlayer.StoppedState deprecation
- Add proper .ico icon for Windows builds
- Version bump to 0.1.2
SPEC

echo "[4/4] Building .rpm package..."
rpmbuild --define "_topdir $RPMBUILD_DIR" -bb "$RPMBUILD_DIR/SPECS/${APP_NAME}.spec"

# Find the built RPM
RPM_FILE=$(find "$RPMBUILD_DIR/RPMS" -name "*.rpm" -type f | head -1)

if [[ -n "$RPM_FILE" && -f "$RPM_FILE" ]]; then
    # Move to project directory
    cp "$RPM_FILE" "$SCRIPT_DIR/"
    RPM_NAME=$(basename "$RPM_FILE")
    SIZE=$(du -h "$SCRIPT_DIR/$RPM_NAME" | cut -f1)

    # Cleanup
    rm -rf "$RPMBUILD_DIR"

    echo ""
    echo "=========================================="
    echo "  Build successful!"
    echo "=========================================="
    echo ""
    echo "  Package: ${RPM_NAME}"
    echo "  Size: ${SIZE}"
    echo ""
    echo "  Install with:"
    echo "    sudo dnf install ./${RPM_NAME}      (Fedora)"
    echo "    sudo zypper install ./${RPM_NAME}   (openSUSE)"
    echo ""
    echo "  NOT TESTED - nemam na cemu da testiram dok ne odradim install Fedore"
    echo ""
else
    echo ""
    echo "ERROR: Build failed!"
    echo "Check output above for errors."
    # Cleanup on failure too
    rm -rf "$RPMBUILD_DIR"
fi
