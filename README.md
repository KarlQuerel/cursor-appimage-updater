# Cursor Updater for Linux

Menu-driven Python application to manage and update Cursor AppImage versions on Linux.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/cursor-updater.git
cd cursor-updater

# Make executable (one-time)
chmod +x cursor_updater.py

# Run it
./cursor_updater.py
```

## Requirements

- **Python 3.7+** (check with `python3 --version`)
- Linux (AppImage format)
- Internet connection

## Usage

After running, you'll see an interactive menu:

- **1** - Check current version and update status
- **2** - Update to latest version
- **3** - Help information
- **4** - Exit

Press `ESC` at any time to exit.

## How It Works

- AppImages stored in: `~/.local/share/cvm/app-images/`
- Active version symlink: `~/.local/share/cvm/active`
- Version cache: `/tmp/cursor_versions.json` (15-minute TTL)

This allows you to keep multiple versions and easily switch between them.

## Alternative Ways to Run

```bash
# Direct execution (recommended)
./cursor_updater.py

# Or as Python module
python3 -m cursor_updater

# Or explicitly with python3
python3 cursor_updater.py
```

## Troubleshooting

**"command not found: python"** → Use `python3` instead

**"Permission denied"** → Run `chmod +x cursor_updater.py`

**No Python installed?** → Install Python 3.7+ from your distribution's package manager:

- Ubuntu/Debian: `sudo apt install python3`
- Fedora: `sudo dnf install python3`
- Arch: `sudo pacman -S python`
