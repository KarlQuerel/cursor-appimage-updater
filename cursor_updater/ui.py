"""User interface components for Cursor Updater."""

import os
import sys
import termios
import tty
from pathlib import Path

from cursor_updater.config import (
    BOLD_BLUE,
    GREEN,
    YELLOW,
    ESC_KEY,
    MENU_OPTIONS,
    MSG_WAIT_KEY,
    MSG_EXITING,
    CURSOR_APPIMAGE,
    DOWNLOADS_DIR,
    PREFIX_WIDTH,
)
from cursor_updater.version import (
    VersionInfo,
    get_version_status,
    get_latest_remote_version,
    get_latest_local_version,
    get_launch_info,
)
from cursor_updater.download import download_version, select_version
from cursor_updater.output import format_message, print_error


def getch() -> str:
    """Read a single character from stdin without requiring Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def getch_timeout(timeout: float = 0.1) -> str:
    """Read a single character with timeout. Returns empty string if timeout."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        new_settings = termios.tcgetattr(fd)
        new_settings[6][termios.VMIN] = 0
        new_settings[6][termios.VTIME] = int(timeout * 10)
        termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
        char = sys.stdin.read(1)
        return char if char else ""
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("clear" if os.name != "nt" else "cls")


def print_header() -> None:
    """Print the application header."""
    header_art = [
        "   ▄▖▖▖▄▖▄▖▄▖▄▖  ▖▖▄▖▄ ▄▖▄▖▄▖▄▖",
        "   ▌ ▌▌▙▘▚ ▌▌▙▘  ▌▌▙▌▌▌▌▌▐ ▙▖▙▘",
        "   ▙▖▙▌▌▌▄▌▙▌▌▌  ▙▌▌ ▙▘▛▌▐ ▙▖▌▌",
    ]
    for line in header_art:
        print(format_message(line, BOLD_BLUE))
    print()


def print_menu() -> None:
    """Print the main menu."""
    print()
    for key, description in MENU_OPTIONS.items():
        print(format_message(f"  {key}. {description}"))
    print()


def wait_for_key(message: str = MSG_WAIT_KEY) -> None:
    """Wait for user to press any key."""
    print(format_message(message), end="", flush=True)
    getch()


def exit_app(message: str = MSG_EXITING) -> None:
    """Exit the application with a message."""
    print(f"\n{format_message(message)}")
    sys.exit(0)


def print_version_info(info: VersionInfo) -> None:
    """Print version information."""
    print()
    print(format_message("Cursor App Information:"))

    if not info.latest_remote:
        print(format_message(f"{'  - 📡 Latest remote version:':<{PREFIX_WIDTH}} (unavailable)"))
        return
    print(
        format_message(
            f"{'  - 📡 Latest remote version:':<{PREFIX_WIDTH}} {info.latest_remote}"
        )
    )
    print(
        format_message(
            f"{'  - 📂 Latest locally available:':<{PREFIX_WIDTH}} {info.latest_local or 'None'}"
        )
    )
    print(
        format_message(
            f"{'  - ⚡ Currently active:':<{PREFIX_WIDTH}} {info.local or 'None'}"
        )
    )


def print_launch_info() -> None:
    """Print information about how Cursor is launched."""
    launch_info = get_launch_info()
    
    print()
    print(format_message("Launch Configuration:", BOLD_BLUE))
    
    def _print_info_line(label: str, value: str, extra_spaces: int = 0) -> None:
        """Helper to print formatted info line."""
        spacing = " " * (1 + extra_spaces)
        print(format_message(f"{label:<{PREFIX_WIDTH}}{spacing}{value}"))
    
    if launch_info["running_from"]:
        _print_info_line("  - 🚀 Running from:", launch_info["running_from"])
    else:
        _print_info_line("  - 🚀 Running from:", "(not running)")
    
    if launch_info["desktop_file_exec"]:
        _print_info_line("  - 🖥️  Desktop launcher:", launch_info["desktop_file_exec"], extra_spaces=2)
    else:
        _print_info_line("  - 🖥️  Desktop launcher:", "(not found)", extra_spaces=2)
    
    if launch_info["symlink_exists"]:
        if launch_info["symlink_target"]:
            _print_info_line("  - 🔗 Symlink target:", launch_info["symlink_target"])
        else:
            _print_info_line("  - 🔗 Symlink:", f"{CURSOR_APPIMAGE} (regular file)")
    else:
        _print_info_line("  - 🔗 Symlink:", f"{CURSOR_APPIMAGE} (does not exist)")
    
    path_status = "✅ Yes" if launch_info["in_path"] else "❌ No"
    _print_info_line("  - 📍 ~/.local/bin in PATH:", path_status)
    
    print()
    if launch_info["running_from"] and launch_info["desktop_file_exec"]:
        running_path = Path(launch_info["running_from"])
        desktop_path = Path(launch_info["desktop_file_exec"]).resolve()
        
        if running_path.resolve() != desktop_path.resolve():
            print(
                format_message(
                    "⚠️  Warning: Running instance and desktop launcher point to different locations",
                    YELLOW
                )
            )
            print(
                format_message(
                    "   Restart Cursor to use the version specified in the desktop launcher."
                )
            )
    
    if not launch_info["in_path"]:
        print(
            format_message(
                "💡 Tip: Add ~/.local/bin to your PATH for command-line access",
                YELLOW
            )
        )


def get_update_status_message(info: VersionInfo) -> str:
    """Determine update status and return formatted message."""
    if not info.local:
        return format_message(
            "💡 No active version. You can install the latest version by pressing 2"
        )

    if info.latest_remote != info.latest_local:
        message = format_message(
            f"🔍 There is a newer Cursor version available for download: {info.latest_remote}",
            YELLOW
        )
        if info.latest_local:
            message += f"\n{format_message(f'   (You have {info.latest_local} locally, you can update to the latest version by pressing 2)')}"
        return message

    if info.latest_remote != info.local:
        return format_message(
            f"🔄 There is a newer version available locally: {info.latest_local}",
            YELLOW
        )

    return format_message("✅ You are running the latest Cursor version!", GREEN)


def check_versions() -> None:
    """Check local vs remote versions."""
    info = get_version_status()
    print_version_info(info)

    if info.latest_remote:
        print(get_update_status_message(info))
    
    print_launch_info()


def update_cursor() -> bool:
    """Update Cursor to latest version."""
    latest_remote = get_latest_remote_version()

    if not latest_remote:
        print_error("Could not determine latest version")
        return False

    latest_local = get_latest_local_version()
    if latest_remote != latest_local:
        if not download_version(latest_remote):
            return False

    return select_version(latest_remote)


def show_help() -> None:
    """Display help information."""
    print()
    print(format_message("📖 Help & Information", BOLD_BLUE))
    print()

    print(format_message("Menu Options:"))
    print("  1. Check Current Setup Information")
    print("     - Shows version info (current, latest local, latest remote)")
    print("     - Displays launch configuration and update status")
    print()
    print("  2. Update Cursor to latest version")
    print("     - Downloads latest version if needed")
    print("     - Updates symlink and desktop launcher")
    print("     - Restart Cursor manually to use the new version")
    print()
    print("  3. Help")
    print("     - Shows this help information")
    print()
    print("  4. Exit")
    print("     - Exits the application")
    print()

    print(format_message("How it works:"))
    print(f"  • Active installation: {CURSOR_APPIMAGE}")
    print(f"  • Downloads stored in: {DOWNLOADS_DIR}")
    print("  • Uses symlinks to manage versions efficiently")
    print("  • Version cache: 15 minutes (auto-refreshes)")
    print()

    print(format_message("Tips:"))
    print("  • Press ESC to exit anytime")
    print("  • Ensure ~/.local/bin is in your PATH for command-line access")
    print("  • Desktop launcher is automatically updated to use managed version")
    print()


def handle_menu_choice(choice: str) -> None:
    """Handle user menu choice."""
    if choice == "1":
        print()
        check_versions()
        print()
        wait_for_key()
    elif choice == "2":
        print()
        update_cursor()
        print()
        wait_for_key()
    elif choice == "3":
        print()
        show_help()
        print()
        wait_for_key()
    elif choice in ("q", "4"):
        exit_app()


def get_user_choice() -> str:
    """Get user menu choice."""
    while True:
        print(format_message("  Press [1-4] to select: "), end="", flush=True)
        choice = getch()

        if ord(choice) == ESC_KEY:
            next_char = getch_timeout(0.15)
            if not next_char:
                exit_app()
            while True:
                char = getch_timeout(0.05)
                if not char:
                    break
            print("\r" + " " * 60 + "\r", end="", flush=True)
            continue

        choice = choice.strip().lower()
        if choice in ("1", "2", "3", "4", "q"):
            print(choice)
            return choice

        print("\r" + " " * 60 + "\r", end="", flush=True)
