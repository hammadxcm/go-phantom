"""Centralized ANSI escape codes for terminal output.

Provides named constants for common foreground colors and text
attributes used by the tail-mode formatter and CLI output.
"""

from __future__ import annotations

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD_YELLOW = "\033[1;33m"
BOLD_RED = "\033[1;31m"
MAGENTA = "\033[0;35m"
BLUE = "\033[0;34m"
