@echo off
REM BalkGrab Windows Build Script
REM Creates a standalone .exe using PyInstaller
REM Run from anywhere - script finds repo root automatically

echo ============================================
echo BalkGrab Windows Build Script
echo ============================================
echo.

REM Change to repo root (parent of build-scripts)
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%.."

echo Working directory: %CD%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo Python found:
python --version

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Install dependencies
echo.
echo Installing/updating dependencies...
pip install --upgrade pip
pip install PySide6 yt-dlp requests

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist "build-scripts\dist" rmdir /s /q "build-scripts\dist"
if exist "build-scripts\build" rmdir /s /q "build-scripts\build"
if exist "build-scripts\BalkGrab.spec" del "build-scripts\BalkGrab.spec"

echo.
echo Building BalkGrab.exe with PyInstaller...
echo.

pyinstaller ^
    --name "BalkGrab" ^
    --onefile ^
    --windowed ^
    --icon "Icons\windows\icon.ico" ^
    --add-data "Icons;Icons" ^
    --hidden-import=PySide6 ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=PySide6.QtMultimedia ^
    --hidden-import=yt_dlp ^
    --hidden-import=requests ^
    --collect-all=yt_dlp ^
    --collect-all=PySide6 ^
    --distpath "build-scripts\dist" ^
    --workpath "build-scripts\build" ^
    --specpath "build-scripts" ^
    --noconfirm ^
    BalkGrab.py

if errorlevel 1 (
    echo.
    echo BUILD FAILED!
    pause
    exit /b 1
)

echo.
echo ============================================
echo Build completed! Looking for ffmpeg...
echo ============================================
echo.

set FFMPEG_FOUND=0

REM 1. Check if ffmpeg is in PATH
where ffmpeg >nul 2>&1
if not errorlevel 1 (
    echo ffmpeg found in PATH - copying to dist...
    for /f "tokens=*" %%f in ('where ffmpeg') do (
        copy /y "%%f" "build-scripts\dist\" >nul 2>&1
        set FFMPEG_FOUND=1
        goto :ffmpeg_done
    )
)

REM 2. Check common install locations
for /d %%d in ("%LOCALAPPDATA%\Programs\ffmpeg*" "%ProgramFiles%\ffmpeg*" "%ProgramFiles(x86)%\ffmpeg*") do (
    if exist "%%d\bin\ffmpeg.exe" (
        echo ffmpeg found at %%d\bin - copying to dist...
        copy /y "%%d\bin\ffmpeg.exe" "build-scripts\dist\" >nul 2>&1
        copy /y "%%d\bin\ffprobe.exe" "build-scripts\dist\" >nul 2>&1
        set FFMPEG_FOUND=1
        goto :ffmpeg_done
    )
)

REM 3. Download ffmpeg automatically via PowerShell
echo ffmpeg not found locally - downloading from GitHub...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$url = 'https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip';" ^
    "$zip = '%TEMP%\ffmpeg_build.zip';" ^
    "$out = '%TEMP%\ffmpeg_extract';" ^
    "Write-Host 'Downloading ffmpeg...';" ^
    "Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing;" ^
    "if (Test-Path $out) { Remove-Item $out -Recurse -Force };" ^
    "Expand-Archive -Path $zip -DestinationPath $out -Force;" ^
    "$ffmpeg = Get-ChildItem $out -Recurse -Filter 'ffmpeg.exe' | Select-Object -First 1;" ^
    "$ffprobe = Get-ChildItem $out -Recurse -Filter 'ffprobe.exe' | Select-Object -First 1;" ^
    "if ($ffmpeg) { Copy-Item $ffmpeg.FullName 'build-scripts\dist\ffmpeg.exe'; Write-Host 'ffmpeg copied.' };" ^
    "if ($ffprobe) { Copy-Item $ffprobe.FullName 'build-scripts\dist\ffprobe.exe'; Write-Host 'ffprobe copied.' };" ^
    "Remove-Item $zip, $out -Recurse -Force -ErrorAction SilentlyContinue"

if exist "build-scripts\dist\ffmpeg.exe" (
    set FFMPEG_FOUND=1
) else (
    echo.
    echo WARNING: ffmpeg download failed!
    echo Download manually from https://ffmpeg.org/download.html
    echo and place ffmpeg.exe + ffprobe.exe next to BalkGrab.exe
)

:ffmpeg_done
echo.
echo ============================================
echo Output: build-scripts\dist\
echo ============================================
dir /b "build-scripts\dist\"
echo.
echo Distribute all files from the dist folder.
echo Users double-click BalkGrab.exe to start.
echo.

pause
