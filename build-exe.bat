@echo off
REM BalkTube Grabber Pro - Windows EXE Build Script
REM Run this on Windows to create a standalone .exe

echo ==========================================
echo   Building BalkTube Grabber Pro for Windows
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.9+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install dependencies
echo [1/4] Installing dependencies...
pip install --quiet PySide6 yt-dlp requests pyinstaller
pip install --quiet --upgrade --pre yt-dlp

REM Create spec file for better control
echo [2/4] Creating build configuration...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo a = Analysis(
echo     ['BalkTube Grabber Pro.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[('Icons', 'Icons')],
echo     hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'PySide6.QtMultimedia'],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     noarchive=False,
echo ^)
echo.
echo pyz = PYZ(a.pure)
echo.
echo exe = EXE(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.datas,
echo     [],
echo     name='BalkTube Grabber Pro',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     runtime_tmpdir=None,
echo     console=False,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     icon='Icons\\icon_256x256.png',
echo ^)
) > balktube.spec

REM Build exe
echo [3/4] Building executable (this may take a few minutes)...
pyinstaller --clean --noconfirm balktube.spec

REM Check result
if exist "dist\BalkTube Grabber Pro.exe" (
    echo.
    echo ==========================================
    echo   Build successful!
    echo ==========================================
    echo.
    echo Output: dist\BalkTube Grabber Pro.exe
    echo.
    echo [4/4] Cleaning up...
    rmdir /s /q build 2>nul
    del balktube.spec 2>nul
    echo.
    echo You can now run: "dist\BalkTube Grabber Pro.exe"
    echo.
    echo NOTE: Make sure FFmpeg is installed and in PATH for audio conversion.
    echo Download FFmpeg: https://ffmpeg.org/download.html
) else (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for errors.
)

echo.
pause
