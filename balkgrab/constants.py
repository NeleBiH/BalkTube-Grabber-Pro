"""App-level constants: paths, semaphores."""

import os
import threading

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Icons are inside the package
ICON_DIR = os.path.join(APP_DIR, "Icons")

# Limit concurrent thumbnail downloads
THUMBNAIL_SEMAPHORE = threading.Semaphore(4)

# Add deno to PATH if available (used by yt-dlp for YouTube JS challenge solving)
_deno_path = os.path.expanduser("~/.deno/bin")
if os.path.isdir(_deno_path) and _deno_path not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _deno_path + os.pathsep + os.environ.get("PATH", "")
