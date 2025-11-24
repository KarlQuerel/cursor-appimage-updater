# Cursor Updater for Linux

Menu-driven Python application to manage and update Cursor AppImage versions on Linux.

## Quick Start

```bash
git clone https://github.com/yourusername/cursor-updater.git
cd cursor-updater
chmod +x cursor_updater.py
./cursor_updater.py
```

## Requirements

- Python 3.7+ (check: `python3 --version`)
- Linux
- Internet connection

## Usage

Interactive menu:

- **1** - Check version status
- **2** - Update to latest version
- **3** - Help
- **4** - Exit

Press `ESC` to exit anytime.

## How It Works

- AppImages: `~/.local/share/cvm/app-images/`
- Active symlink: `~/.local/share/cvm/active`
- Cache: `/tmp/cursor_versions.json` (15-min TTL)

## Troubleshooting

**"command not found: python"**

```bash
python3 cursor_updater.py
```

**"Permission denied"**

```bash
chmod +x cursor_updater.py
```

**Python not installed**

```bash
# Ubuntu/Debian
sudo apt install python3

# Fedora
sudo dnf install python3

# Arch
sudo pacman -S python
```
