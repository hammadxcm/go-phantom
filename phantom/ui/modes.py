"""Output mode enum for Phantom."""

from __future__ import annotations

from enum import Enum


class OutputMode(Enum):
    """Selects how Phantom displays status and log output."""

    TRAY = "tray"  # default: tray icon + stdout logging
    TUI = "tui"  # Rich dashboard
    TAIL = "tail"  # streaming colored logs
    GHOST = "ghost"  # silent, file-only logging
    GUI = "gui"  # tkinter GUI window
