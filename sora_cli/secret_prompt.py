"""
S0RA CLI Secret Prompt — Masked input for API keys and passwords.
Mirrors hermes_cli/secret_prompt.py from Hermes Agent.
"""

import sys
import termios
import tty
from typing import Optional


def masked_secret_prompt(prompt: str = "", mask_char: str = "•") -> str:
    """
    Prompt for a secret with masked input (shows mask_char instead of typed chars).
    Press Enter to confirm, Ctrl+C to cancel.
    """
    if not sys.stdin.isatty():
        # Fallback for non-interactive
        return input(prompt)

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        # Print prompt without newline
        sys.stdout.write(prompt)
        sys.stdout.flush()

        # Set terminal to raw mode
        tty.setraw(fd)

        chars = []
        while True:
            ch = sys.stdin.read(1)
            if ch == "\n" or ch == "\r":
                sys.stdout.write("\n")
                break
            elif ch == "\x03":  # Ctrl+C
                sys.stdout.write("\n")
                raise KeyboardInterrupt
            elif ch == "\x7f" or ch == "\b":  # Backspace
                if chars:
                    chars.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif ch == "\x1b":  # Escape sequence (arrow keys, etc.)
                # Read and discard the rest of the escape sequence
                sys.stdin.read(2)
            elif ch.isprintable():
                chars.append(ch)
                sys.stdout.write(mask_char)
                sys.stdout.flush()
            # Ignore other control characters

        return "".join(chars)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# Windows fallback
try:
    import msvcrt

    def _masked_secret_prompt_windows(prompt: str = "", mask_char: str = "•") -> str:
        sys.stdout.write(prompt)
        sys.stdout.flush()
        chars = []
        while True:
            ch = msvcrt.getwch()
            if ch == "\r":
                sys.stdout.write("\n")
                break
            elif ch == "\x03":  # Ctrl+C
                sys.stdout.write("\n")
                raise KeyboardInterrupt
            elif ch == "\b":  # Backspace
                if chars:
                    chars.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif ch == "\x00" or ch == "\xe0":  # Special keys (arrows, etc.)
                msvcrt.getwch()  # Discard next char
            elif ch.isprintable():
                chars.append(ch)
                sys.stdout.write(mask_char)
                sys.stdout.flush()
        return "".join(chars)

    if sys.platform == "win32":
        masked_secret_prompt = _masked_secret_prompt_windows  # type: ignore

except ImportError:
    pass  # Use the termios version on Unix