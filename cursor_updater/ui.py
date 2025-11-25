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
    NC,
    BOLD,
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
    print()
    header_art = [
        "      ▄▖▖▖▄▖▄▖▄▖▄▖  ▖▖▄▖▄ ▄▖▄▖▄▖▄▖",
        "      ▌ ▌▌▙▘▚ ▌▌▙▘  ▌▌▙▌▌▌▌▌▐ ▙▖▙▘",
        "      ▙▖▙▌▌▌▄▌▙▌▌▌  ▙▌▌ ▙▘▛▌▐ ▙▖▌▌",
    ]
    for line in header_art:
        print(format_message(line, BOLD_BLUE))
    print()


def draw_box_top(width: int) -> str:
    """Draw top border of a retro pixel box."""
    return "╔" + "═" * (width - 2) + "╗"


def draw_box_bottom(width: int) -> str:
    """Draw bottom border of a retro pixel box."""
    return "╚" + "═" * (width - 2) + "╝"


def draw_box_line(content: str, width: int) -> str:
    """Draw a line inside a retro pixel box."""
    padding = width - len(content) - 2
    return "║" + content + " " * padding + "║"


def _print_menu_line(line: str, width: int) -> None:
    """Print a single menu line with borders."""
    print(format_message("║", BOLD_BLUE), end="")
    print(f"{BOLD} {line}{NC}", end="")
    padding = width - len(line) - 3
    print(" " * padding + format_message("║", BOLD_BLUE))


def print_menu() -> None:
    """Print the main menu with retro pixel borders."""
    menu_lines = [f"  {key}. {description}" for key, description in MENU_OPTIONS.items()]
    width = max(len(line) for line in menu_lines) + 4
    
    print(format_message(draw_box_top(width), BOLD_BLUE))
    for line in menu_lines:
        _print_menu_line(line, width)
    print(format_message(draw_box_bottom(width), BOLD_BLUE))
    print()


def wait_for_key(message: str = MSG_WAIT_KEY) -> None:
    """Wait for user to press any key."""
    print(format_message(message), end="", flush=True)
    getch()


def exit_app(message: str = MSG_EXITING) -> None:
    """Exit the application with a message."""
    print(f"\n{format_message(message)}")
    sys.exit(0)


def _print_info_line(label: str, value: str) -> None:
    """Print a formatted info line with consistent spacing."""
    print(format_message(f"{label:<{PREFIX_WIDTH}} {value}"))


def print_version_info(info: VersionInfo) -> None:
    """Print version information."""
    print()
    print(format_message("Cursor App Information:"))

    if not info.latest_remote:
        _print_info_line("  - 📡 Latest remote version:", "(unavailable)")
        return
    
    _print_info_line("  - 📡 Latest remote version:", info.latest_remote)
    _print_info_line("  - 📂 Latest locally available:", info.latest_local or "None")
    _print_info_line("  - ⚡ Currently active:", info.local or "None")


def _print_label_value(label: str, value: str) -> None:
    """Print a label and value on separate lines."""
    print(format_message(label))
    print(f"    {value}")


def _print_warnings_and_tips(launch_info: dict) -> None:
    """Print warnings and tips based on launch configuration."""
    running_path = launch_info.get("running_from")
    desktop_path = launch_info.get("desktop_file_exec")
    
    if running_path and desktop_path:
        if Path(running_path).resolve() != Path(desktop_path).resolve():
            print(format_message(
                "⚠️  Warning: Running instance and desktop launcher point to different locations",
                YELLOW
            ))
            print(format_message(
                "   Restart Cursor to use the version specified in the desktop launcher."
            ))
            print()
    
    if not launch_info["in_path"]:
        print(format_message(
            "💡 Tip: Add ~/.local/bin to your PATH for command-line access",
            YELLOW
        ))
        print()


def print_launch_info() -> None:
    """Print information about how Cursor is launched."""
    launch_info = get_launch_info()
    
    print()
    print(format_message("Launch Configuration:", BOLD_BLUE))
    print()
    
    print(format_message("  Runtime:"))
    _print_label_value(
        "  - 🚀 Running from:",
        launch_info.get("running_from") or "(not running)"
    )
    print()
    
    print(format_message("  Configuration:"))
    _print_label_value(
        "  - 🖥️  Desktop launcher:",
        launch_info.get("desktop_file_exec") or "(not found)"
    )
    
    if launch_info["symlink_exists"]:
        symlink_value = launch_info.get("symlink_target") or f"{CURSOR_APPIMAGE} (regular file)"
    else:
        symlink_value = f"{CURSOR_APPIMAGE} (does not exist)"
    _print_label_value("  - 🔗 Symlink:", symlink_value)
    print()
    
    print(format_message("  Environment:"))
    path_status = "✅ Yes" if launch_info["in_path"] else "❌ No"
    print(format_message(f"  - 📍 ~/.local/bin in PATH: {path_status}"))
    print()
    
    _print_warnings_and_tips(launch_info)


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
            local_note = f"   (You have {info.latest_local} locally, you can update to the latest version by pressing 2)"
            message += f"\n{format_message(local_note)}"
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
    menu_actions = {
        "1": check_versions,
        "2": update_cursor,
        "3": show_help,
    }
    
    if choice in menu_actions:
        print()
        menu_actions[choice]()
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
