"""
S0RA CLI Curses UI — Arrow-key menus for setup wizard.
Mirrors hermes_cli/curses_ui.py from Hermes Agent.
"""

import curses
from typing import List, Optional, Set


def curses_radiolist(
    question: str,
    choices: List[str],
    selected: int = 0,
    cancel_returns: int = -1,
    description: Optional[str] = None,
) -> int:
    """
    Single-select radio list using curses.
    Returns the selected index, or cancel_returns on Escape/Ctrl+C.
    """
    def _inner(stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()

        # Color pairs
        curses.init_pair(1, curses.COLOR_CYAN, -1)    # header
        curses.init_pair(2, curses.COLOR_GREEN, -1)   # selected
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # description
        curses.init_pair(4, curses.COLOR_WHITE, -1)   # normal

        current = selected
        height, width = stdscr.getmaxyx()

        while True:
            stdscr.clear()

            # Header
            stdscr.addstr(0, 0, question[:width-1], curses.color_pair(1) | curses.A_BOLD)
            if description:
                stdscr.addstr(1, 0, description[:width-1], curses.color_pair(3))

            # Choices
            for i, choice in enumerate(choices):
                y = i + (3 if description else 2)
                if y >= height - 1:
                    break

                marker = "●" if i == current else "○"
                prefix = f"  {marker} "
                text = f"{prefix}{choice}"

                if i == current:
                    stdscr.addstr(y, 0, text[:width-1], curses.color_pair(2) | curses.A_BOLD)
                else:
                    stdscr.addstr(y, 0, text[:width-1], curses.color_pair(4))

            # Footer
            footer_y = height - 1
            stdscr.addstr(footer_y, 0, "↑/↓: Navigate  Enter: Select  Esc: Cancel".ljust(width-1), curses.color_pair(3))

            stdscr.refresh()

            key = stdscr.getch()
            if key in (curses.KEY_UP, ord('k')):
                current = (current - 1) % len(choices)
            elif key in (curses.KEY_DOWN, ord('j')):
                current = (current + 1) % len(choices)
            elif key in (curses.KEY_ENTER, 10, 13):  # Enter
                return current
            elif key == 27:  # Escape
                return cancel_returns

    try:
        return curses.wrapper(_inner)
    except Exception:
        # Fallback: return default
        return cancel_returns


def curses_checklist(
    title: str,
    items: List[str],
    pre_selected: Set[int],
    cancel_returns: Optional[Set[int]] = None,
) -> Set[int]:
    """
    Multi-select checklist using curses.
    Space toggles, Enter on "Continue →" confirms.
    Returns set of selected indices.
    """
    if cancel_returns is None:
        cancel_returns = set(pre_selected)

    # Add "Continue →" option
    display_items = items + ["Continue →"]
    continue_idx = len(items)
    selected = set(pre_selected)

    def _inner(stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(1, curses.COLOR_CYAN, -1)    # header
        curses.init_pair(2, curses.COLOR_GREEN, -1)   # selected
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # description/continue
        curses.init_pair(4, curses.COLOR_WHITE, -1)   # normal
        curses.init_pair(5, curses.COLOR_MAGENTA, -1) # checked

        current = 0
        height, width = stdscr.getmaxyx()

        while True:
            stdscr.clear()

            stdscr.addstr(0, 0, title[:width-1], curses.color_pair(1) | curses.A_BOLD)

            for i, item in enumerate(display_items):
                y = i + 2
                if y >= height - 1:
                    break

                if i == continue_idx:
                    marker = "→"
                    prefix = f"  {marker} "
                    text = f"{prefix}{item}"
                    attr = curses.color_pair(3) | curses.A_BOLD
                else:
                    marker = "☑" if i in selected else "☐"
                    prefix = f"  {marker} "
                    text = f"{prefix}{item}"
                    if i in selected:
                        attr = curses.color_pair(5) | curses.A_BOLD
                    elif i == current:
                        attr = curses.color_pair(2) | curses.A_BOLD
                    else:
                        attr = curses.color_pair(4)

                stdscr.addstr(y, 0, text[:width-1], attr)

            # Footer
            footer_y = height - 1
            stdscr.addstr(footer_y, 0, "↑/↓: Navigate  Space: Toggle  Enter: Confirm  Esc: Cancel".ljust(width-1), curses.color_pair(3))

            stdscr.refresh()

            key = stdscr.getch()
            if key in (curses.KEY_UP, ord('k')):
                current = (current - 1) % len(display_items)
            elif key in (curses.KEY_DOWN, ord('j')):
                current = (current + 1) % len(display_items)
            elif key == ord(' '):  # Space
                if current != continue_idx:
                    if current in selected:
                        selected.remove(current)
                    else:
                        selected.add(current)
            elif key in (curses.KEY_ENTER, 10, 13):  # Enter
                if current == continue_idx:
                    return selected
            elif key == 27:  # Escape
                return cancel_returns

    try:
        return curses.wrapper(_inner)
    except Exception:
        return cancel_returns