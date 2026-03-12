"""App-to-shortcut mapping registry for tab switching."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pynput.keyboard import Key, KeyCode

from phantom.core.platform import OS


@dataclass(frozen=True)
class TabShortcut:
    """Key combination for switching tabs forward and backward.

    Attributes:
        forward: Keys to press for switching to the next tab.
        backward: Keys to press for switching to the previous tab.
    """

    forward: tuple[Key | KeyCode, ...]
    backward: tuple[Key | KeyCode, ...]


# macOS shortcuts
_MAC_CMD_BRACKET = TabShortcut(
    forward=(Key.cmd, Key.shift, KeyCode.from_char("]")),
    backward=(Key.cmd, Key.shift, KeyCode.from_char("[")),
)
_CTRL_TAB = TabShortcut(
    forward=(Key.ctrl, Key.tab),
    backward=(Key.ctrl, Key.shift, Key.tab),
)
_KITTY = TabShortcut(
    forward=(Key.ctrl, Key.shift, Key.right),
    backward=(Key.ctrl, Key.shift, Key.left),
)
_GNOME_KONSOLE = TabShortcut(
    forward=(Key.ctrl, Key.page_down),
    backward=(Key.ctrl, Key.page_up),
)

# Registry: list of (pattern, {OS: TabShortcut})
# Longer/more-specific patterns first to avoid false matches.
_REGISTRY: list[tuple[str, dict[OS, TabShortcut]]] = [
    # Browsers
    (
        "chrome|firefox|safari|edge|brave|arc|opera|chromium",
        {
            OS.MACOS: _MAC_CMD_BRACKET,
            OS.WINDOWS: _CTRL_TAB,
            OS.LINUX: _CTRL_TAB,
        },
    ),
    # VS Code / Cursor (uses Ctrl+Tab on all platforms)
    (
        "code|cursor",
        {
            OS.MACOS: _CTRL_TAB,
            OS.WINDOWS: _CTRL_TAB,
            OS.LINUX: _CTRL_TAB,
        },
    ),
    # macOS terminals
    (
        "iterm",
        {OS.MACOS: _MAC_CMD_BRACKET},
    ),
    # kitty (cross-platform)
    (
        "kitty",
        {
            OS.MACOS: _KITTY,
            OS.WINDOWS: _KITTY,
            OS.LINUX: _KITTY,
        },
    ),
    # wezterm (cross-platform)
    (
        "wezterm",
        {
            OS.MACOS: _CTRL_TAB,
            OS.WINDOWS: _CTRL_TAB,
            OS.LINUX: _CTRL_TAB,
        },
    ),
    # Windows Terminal (check before generic "terminal")
    (
        "windows terminal|windowsterminal|wt\\.exe|wt$",
        {OS.WINDOWS: _CTRL_TAB},
    ),
    # GNOME Terminal / Konsole
    (
        "gnome-terminal|konsole",
        {OS.LINUX: _GNOME_KONSOLE},
    ),
    # macOS Terminal.app (generic "terminal" last)
    (
        "terminal",
        {OS.MACOS: _MAC_CMD_BRACKET},
    ),
]

_DEFAULT = _CTRL_TAB


def lookup_shortcut(app_name: str, os: OS) -> TabShortcut:
    """Return the best tab-switching shortcut for an application.

    Matches *app_name* against the internal registry of known
    applications and falls back to Ctrl+Tab if no match is found.

    Args:
        app_name: Application name or window title to match.
        os: Current operating system.

    Returns:
        The ``TabShortcut`` with forward/backward key combos.
    """
    normalized = re.sub(r"[\s._-]+", "-", app_name.lower())
    for pattern, shortcuts in _REGISTRY:
        if re.search(pattern, normalized) and os in shortcuts:
            return shortcuts[os]
    return _DEFAULT
