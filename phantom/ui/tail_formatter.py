"""ANSI color formatter for tail mode streaming logs."""

from __future__ import annotations

import logging

from phantom.ui.ansi import BLUE, BOLD_RED, BOLD_YELLOW, CYAN, DIM, GREEN, MAGENTA, RESET, YELLOW

_SIM_COLORS: dict[str, str] = {
    "phantom.simulators.mouse": CYAN,
    "phantom.simulators.keyboard": GREEN,
    "phantom.simulators.scroll": YELLOW,
    "phantom.simulators.app_switcher": MAGENTA,
    "phantom.simulators.browser_tabs": BLUE,
    "phantom.simulators.code_typing": GREEN,
}


class TailFormatter(logging.Formatter):
    """Colorizes log output based on simulator logger name and log level.

    Error and warning messages receive bold highlight colors; simulator
    messages are tinted per-simulator; everything else is dimmed.
    """

    def __init__(self) -> None:
        """Initialize with a short timestamp format."""
        super().__init__(fmt="%(asctime)s %(name)s: %(message)s", datefmt="%H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with ANSI color codes.

        Args:
            record: The log record to format.

        Returns:
            The colorized log string.
        """
        msg = super().format(record)
        if record.levelno >= logging.ERROR:
            return f"{BOLD_RED}{msg}{RESET}"
        if record.levelno >= logging.WARNING:
            return f"{BOLD_YELLOW}{msg}{RESET}"
        color = _SIM_COLORS.get(record.name)
        if color:
            return f"{color}{msg}{RESET}"
        return f"{DIM}{msg}{RESET}"
