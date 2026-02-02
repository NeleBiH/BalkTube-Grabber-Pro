#!/bin/bash
# BalkTube Grabber Pro - Run Script-This will enable you to run app with no install

APP_NAME="BalkTube Grabber Pro"
INSTALL_DIR="$HOME/.balktube"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add deno to PATH if available
if [[ -d "$HOME/.deno/bin" ]]; then
    export PATH="$HOME/.deno/bin:$PATH"
fi

# Function to run from a directory
run_app() {
    local dir="$1"
    local venv="$dir/.venv"
    local app="$dir/BalkTube Grabber Pro.py"

    if [[ -f "$app" && -d "$venv" ]]; then
        echo "Starting $APP_NAME from: $dir"
        exec "$venv/bin/python" "$app" "$@"
    fi
    return 1
}

# Try installed location first
if [[ -f "$INSTALL_DIR/BalkTube Grabber Pro.py" ]]; then
    run_app "$INSTALL_DIR" "$@"
fi

# Try project directory (where this script is located)
if [[ -f "$SCRIPT_DIR/BalkTube Grabber Pro.py" ]]; then
    # Check if venv exists in project directory
    if [[ -d "$SCRIPT_DIR/.venv" ]]; then
        run_app "$SCRIPT_DIR" "$@"
    else
        echo "Virtual environment not found in project directory."
        echo "Creating virtual environment..."
        python3 -m venv "$SCRIPT_DIR/.venv"
        "$SCRIPT_DIR/.venv/bin/pip" install --quiet PySide6 yt-dlp requests Pillow
        "$SCRIPT_DIR/.venv/bin/pip" install --quiet --upgrade --pre yt-dlp
        run_app "$SCRIPT_DIR" "$@"
    fi
fi

# Not found anywhere
echo "Error: $APP_NAME not found!"
echo ""
echo "Searched locations:"
echo "  - $INSTALL_DIR (installed)"
echo "  - $SCRIPT_DIR (project)"
echo ""
echo "Please run install.sh first or make sure you're in the project directory."
exit 1
