"""
S0RA CLI Output — Standardized output functions.
Mirrors hermes_cli/cli_output.py from Hermes Agent.
"""

from sora_cli.colors import color, Colors


def print_error(msg: str) -> None:
    """Print an error message in red."""
    print(color(f"✗ {msg}", Colors.RED, Colors.BOLD))


def print_success(msg: str) -> None:
    """Print a success message in green."""
    print(color(f"✓ {msg}", Colors.GREEN, Colors.BOLD))


def print_warning(msg: str) -> None:
    """Print a warning message in yellow."""
    print(color(f"⚠ {msg}", Colors.YELLOW, Colors.BOLD))


def print_info(msg: str) -> None:
    """Print an info message in cyan."""
    print(color(f"ℹ {msg}", Colors.CYAN))


def print_dim(msg: str) -> None:
    """Print a dim message."""
    print(color(msg, Colors.DIM))


def print_header(title: str) -> None:
    """Print a section header."""
    print()
    print(color(f"◆ {title}", Colors.CYAN, Colors.BOLD))


def print_kv(key: str, value: str, key_color: str = Colors.CYAN, val_color: str = Colors.WHITE) -> None:
    """Print a key-value pair."""
    print(f"  {color(key, key_color)}: {color(value, val_color)}")