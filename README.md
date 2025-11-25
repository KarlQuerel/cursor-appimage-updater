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

- **Linux** (AppImages are Linux-specific)
- **Python 3.7+**
- **Internet connection**

All operations run in user space - **no sudo/root required**.

## Usage

Interactive menu:
- **1** - Check version status and launch configuration
- **2** - Update/Install to latest version
- **3** - Help
- **4** - Exit

Press `ESC` to exit anytime.

## How It Works

- Downloads: `~/.local/share/cursor-updater/app-images/cursor-{version}.AppImage`
- Active: `~/.local/bin/cursor.AppImage` → symlink to selected version
- Automatically updates desktop launcher
- Version cache: 15 minutes (auto-refreshes)

Uses symlinks to manage versions efficiently without duplicating large files.

## Troubleshooting

**Python not found**: Use `python3 cursor_updater.py`

**Cursor not launching**:
1. Ensure `~/.local/bin/` is in PATH:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
   ```
