#!/usr/bin/env python3
"""Simple Cursor AppImage Updater for Linux"""

from config import DOWNLOADS_DIR
from ui import (
    clear_screen,
    print_header,
    print_menu,
    get_user_choice,
    handle_menu_choice,
)


def main() -> None:
    """Main entry point."""
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        clear_screen()
        print_header()
        print_menu()
        choice = get_user_choice()
        handle_menu_choice(choice)


if __name__ == "__main__":
    main()
