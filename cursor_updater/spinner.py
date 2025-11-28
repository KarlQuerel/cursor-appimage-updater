"""Spinner utility for displaying loading indicators."""

import sys
import termios
import threading
from contextlib import contextmanager
from typing import Optional

from cursor_updater.config import BOLD, NC, YELLOW


# Constants
FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
FRAME_INTERVAL = 0.1
INDENT = "  "
THREAD_JOIN_TIMEOUT = 0.5


class InputBlocker:
    """Context manager to temporarily disable terminal input."""

    def __init__(self, stdin_fd: int):
        self.stdin_fd = stdin_fd
        self.old_settings: Optional[list] = None

    def __enter__(self) -> "InputBlocker":
        """Disable stdin input."""
        try:
            self.old_settings = termios.tcgetattr(self.stdin_fd)
            termios.tcflush(self.stdin_fd, termios.TCIFLUSH)
            settings = termios.tcgetattr(self.stdin_fd)
            settings[3] &= ~(termios.ICANON | termios.ECHO)
            settings[6][termios.VMIN] = 0
            settings[6][termios.VTIME] = 0
            termios.tcsetattr(self.stdin_fd, termios.TCSADRAIN, settings)
        except (OSError, AttributeError):
            self.old_settings = None
        return self

    def __exit__(self, *args) -> None:
        """Restore stdin input."""
        if self.old_settings:
            try:
                termios.tcsetattr(self.stdin_fd, termios.TCSADRAIN, self.old_settings)
            except (OSError, AttributeError):
                pass


def _format_spinner_text(frame: str, message: str) -> str:
    """Format spinner text with frame and message."""
    return f"{INDENT}{frame} {message}"


def _format_ansi_text(text: str) -> str:
    """Format text with ANSI color codes."""
    return f"{BOLD}{YELLOW}{text}{NC}"


class Spinner:
    """A rotating spinner with customizable message."""

    def __init__(self, message: str = "Thinking", stream=sys.stdout):
        self.message = message
        self.stream = stream
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.frame_index = 0

    def _animate(self) -> None:
        """Animate the spinner in a separate thread."""
        while not self.stop_event.is_set():
            frame = FRAMES[self.frame_index]
            self.frame_index = (self.frame_index + 1) % len(FRAMES)
            text = _format_spinner_text(frame, self.message)
            self.stream.write(f"\r{_format_ansi_text(text)}")
            self.stream.flush()
            self.stop_event.wait(FRAME_INTERVAL)

    def _clear(self) -> None:
        """Clear the spinner line."""
        text = _format_spinner_text(FRAMES[0], self.message)
        self.stream.write(f"\r{' ' * len(text)}\r\n")
        self.stream.flush()

    def start(self) -> None:
        """Start spinner animation and disable input."""
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self, clear: bool = True) -> None:
        """Stop spinner animation."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=THREAD_JOIN_TIMEOUT)
        if clear:
            self._clear()

    def __enter__(self) -> "Spinner":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, *args) -> bool:
        """Context manager exit."""
        self.stop()
        return False


@contextmanager
def show_spinner(message: str = "Thinking"):
    """Context manager for displaying a spinner during an operation."""
    with InputBlocker(sys.stdin.fileno()):
        spinner = Spinner(message)
        try:
            spinner.start()
            yield
        finally:
            spinner.stop()
