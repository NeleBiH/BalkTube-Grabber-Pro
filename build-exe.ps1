# BalkTube Grabber Pro - Windows EXE Build Script (PowerShell)
# Run: powershell -ExecutionPolicy Bypass -File build-exe.ps1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Building BalkTube Grabber Pro for Windows" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host "[1/4] Installing dependencies..." -ForegroundColor Yellow
pip install --quiet PySide6 yt-dlp requests pyinstaller 2>$null
pip install --quiet --upgrade --pre yt-dlp 2>$null

# Build with PyInstaller
Write-Host "[2/4] Building executable (this may take a few minutes)..." -ForegroundColor Yellow

$pyinstallerArgs = @(
    "--onefile",
    "--windowed",
    "--name=BalkTube Grabber Pro",
    "--icon=Icons\icon_256x256.png",
    "--add-data=Icons;Icons",
    "--hidden-import=PySide6.QtCore",
    "--hidden-import=PySide6.QtGui",
    "--hidden-import=PySide6.QtWidgets",
    "--hidden-import=PySide6.QtMultimedia",
    "--clean",
    "--noconfirm",
    "BalkTube Grabber Pro.py"
)

pyinstaller @pyinstallerArgs

# Check result
$exePath = "dist\BalkTube Grabber Pro.exe"
if (Test-Path $exePath) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "  Build successful!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""

    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Host "Output: $exePath" -ForegroundColor Cyan
    Write-Host "Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""

    # Cleanup
    Write-Host "[3/4] Cleaning up..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue
    Remove-Item -Force "*.spec" -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "[4/4] Done!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run: `"$exePath`"" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "NOTE: Make sure FFmpeg is installed for audio conversion." -ForegroundColor Yellow
    Write-Host "Download: https://ffmpeg.org/download.html" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    Write-Host "Check the output above for errors." -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
