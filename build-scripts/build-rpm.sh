#!/bin/bash
# Build .rpm package for BalkGrab
# Requires: rpmbuild (rpm-build package)
# Usage: ./build-rpm.sh

set -e

APP_NAME="balkgrab"
APP_VERSION="0.3.0"
ARCH="x86_64"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_ROOT="$SCRIPT_DIR/build/rpm"
OUTPUT_DIR="$SCRIPT_DIR/dist"

echo "=========================================="
echo "  Building .rpm package"
echo "  ${APP_NAME} v${APP_VERSION}"
echo "=========================================="

# Check dependencies
if ! command -v rpmbuild &>/dev/null; then
    echo "Error: rpmbuild not found."
    echo "  Fedora/RHEL: sudo dnf install rpm-build"
    echo "  openSUSE:    sudo zypper install rpm-build"
    exit 1
fi

# Clean previous build
rm -rf "$BUILD_ROOT"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$BUILD_ROOT"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create tarball
TARBALL_DIR="${APP_NAME}-${APP_VERSION}"
TARBALL_PATH="$BUILD_ROOT/SOURCES/${TARBALL_DIR}.tar.gz"

TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/$TARBALL_DIR"
cp "$PROJECT_DIR/BalkGrab.py" "$TMPDIR/$TARBALL_DIR/"
cp "$PROJECT_DIR/requirements.txt" "$TMPDIR/$TARBALL_DIR/"
cp -r "$PROJECT_DIR/Icons" "$TMPDIR/$TARBALL_DIR/"
tar -czf "$TARBALL_PATH" -C "$TMPDIR" "$TARBALL_DIR"
rm -rf "$TMPDIR"

# Create spec file
cat > "$BUILD_ROOT/SPECS/${APP_NAME}.spec" << SPEC
Name:           ${APP_NAME}
Version:        ${APP_VERSION}
Release:        1%{?dist}
Summary:        YouTube Downloader with GUI
License:        MIT
URL:            https://github.com/NeleBiH/BalkGrab
Source0:        %{name}-%{version}.tar.gz

Requires:       python3 >= 3.9
Requires:       ffmpeg-free
BuildArch:      noarch

%description
BalkGrab - Free & Open Source YouTube downloader with GUI.
Search, preview, and download videos/audio from YouTube.
Built with PySide6 and yt-dlp.

%prep
%setup -q

%install
mkdir -p %{buildroot}/opt/balkgrab
mkdir -p %{buildroot}/%{_bindir}
mkdir -p %{buildroot}/%{_datadir}/applications

cp BalkGrab.py %{buildroot}/opt/balkgrab/
cp requirements.txt %{buildroot}/opt/balkgrab/
cp -r Icons %{buildroot}/opt/balkgrab/

# Icons
for size in 16 32 48 64 128 256; do
    mkdir -p %{buildroot}/%{_datadir}/icons/hicolor/\${size}x\${size}/apps
    if [ -f Icons/linux/icon_\${size}x\${size}.png ]; then
        cp Icons/linux/icon_\${size}x\${size}.png \
           %{buildroot}/%{_datadir}/icons/hicolor/\${size}x\${size}/apps/balkgrab.png
    fi
done

# Launcher
cat > %{buildroot}/%{_bindir}/balkgrab << 'LAUNCHER'
#!/bin/bash
INSTALL_DIR="/opt/balkgrab"
if [[ ! -d "\$INSTALL_DIR/.venv" ]]; then
    echo "First run: setting up Python environment..."
    python3 -m venv "\$INSTALL_DIR/.venv"
    "\$INSTALL_DIR/.venv/bin/pip" install --quiet -r "\$INSTALL_DIR/requirements.txt"
    "\$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade --pre yt-dlp
fi
exec "\$INSTALL_DIR/.venv/bin/python" "\$INSTALL_DIR/BalkGrab.py" "\$@"
LAUNCHER
chmod +x %{buildroot}/%{_bindir}/balkgrab

# Desktop entry
cat > %{buildroot}/%{_datadir}/applications/balkgrab.desktop << 'DESKTOP'
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
DESKTOP

%post
python3 -m venv /opt/balkgrab/.venv 2>/dev/null || true
/opt/balkgrab/.venv/bin/pip install --quiet -r /opt/balkgrab/requirements.txt 2>/dev/null || true
/opt/balkgrab/.venv/bin/pip install --quiet --upgrade --pre yt-dlp 2>/dev/null || true
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor 2>/dev/null || true
update-desktop-database %{_datadir}/applications 2>/dev/null || true

%postun
rm -rf /opt/balkgrab/.venv
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor 2>/dev/null || true
update-desktop-database %{_datadir}/applications 2>/dev/null || true

%files
/opt/balkgrab/
%{_bindir}/balkgrab
%{_datadir}/applications/balkgrab.desktop
%{_datadir}/icons/hicolor/*/apps/balkgrab.png

SPEC

# Build RPM
rpmbuild --define "_topdir $BUILD_ROOT" -bb "$BUILD_ROOT/SPECS/${APP_NAME}.spec"

# Copy output
RPM_FILE=$(find "$BUILD_ROOT/RPMS" -name "*.rpm" -type f | head -1)
if [[ -n "$RPM_FILE" ]]; then
    cp "$RPM_FILE" "$OUTPUT_DIR/"
    echo ""
    echo "=========================================="
    echo "  Build complete!"
    echo "  Output: $OUTPUT_DIR/$(basename "$RPM_FILE")"
    echo "=========================================="
    echo ""
    echo "  Install with: sudo dnf install $OUTPUT_DIR/$(basename "$RPM_FILE")"
else
    echo "Error: RPM file not found after build!"
    exit 1
fi
