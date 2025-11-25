"""Configuration constants for Cursor Updater."""

from pathlib import Path
import re

# Directory paths
CURSOR_APPIMAGE = Path.home() / ".local" / "bin" / "cursor.AppImage"
DOWNLOADS_DIR = Path.home() / ".local" / "share" / "cursor-updater" / "app-images"
CACHE_FILE = Path("/tmp/cursor_versions.json")

# Cache settings
CACHE_MAX_AGE = 15 * 60  # 15 minutes

# Network settings
VERSION_HISTORY_URL = (
    "https://raw.githubusercontent.com/oslook/cursor-ai-downloads/"
    "refs/heads/main/version-history.json"
)
CHUNK_SIZE = 8192
DOWNLOAD_TIMEOUT = 30
REQUEST_TIMEOUT = 10
USER_AGENT = "Cursor-Updater/1.0"

# ANSI color codes
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
NC = "\033[0m"
BOLD = "\033[1m"
BOLD_BLUE = "\033[1;34m"

# Patterns
VERSION_PATTERN = re.compile(r"cursor-([0-9.]+)\.AppImage")

# UI settings
ESC_KEY = 27
PREFIX_WIDTH = 33
DESKTOP_FILE = Path.home() / ".local" / "share" / "applications" / "cursor.desktop"

# Menu options
MENU_OPTIONS = {
    "1": "Check Current Setup Information",
    "2": "Update Cursor to latest version",
    "3": "Help",
    "4": "Exit",
}

# Messages
MSG_WAIT_KEY = "Press any key to return to menu..."
MSG_EXITING = "Exiting..."
