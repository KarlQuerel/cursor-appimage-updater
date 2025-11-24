"""Output formatting and printing utilities."""

from config import BOLD, GREEN, RED, NC


def format_message(message: str, color: str = "") -> str:
    """Format a message with color and bold."""
    return f"{BOLD}{color}{message}{NC}"


def print_error(message: str) -> None:
    """Print an error message in red and bold."""
    print(format_message(f"❌ {message}", RED))


def print_success(message: str) -> None:
    """Print a success message in green and bold."""
    print(format_message(f"✅ {message}", GREEN))


def print_info(message: str) -> None:
    """Print an info message in bold."""
    print(format_message(message))
