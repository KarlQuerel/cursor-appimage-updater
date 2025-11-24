"""Main entry point for Cursor Updater."""

from cursor_updater.config import DOWNLOADS_DIR
from cursor_updater.ui import (
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
