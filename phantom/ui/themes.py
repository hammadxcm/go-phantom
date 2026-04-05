"""Color themes for the TUI dashboard.

Each theme is a dictionary of Rich style strings keyed by UI element
name. Themes control header, panel, status, and per-simulator colors.
"""

from __future__ import annotations

from typing import Any

#: Type alias for a theme configuration dictionary.
Theme = dict[str, Any]

#: Built-in theme definitions keyed by name.
THEMES: dict[str, Theme] = {
    "default": {
        "header_style": "bold blue",
        "panel_border": "blue",
        "title_style": "bold cyan",
        "sim_colors": {
            "mouse": "cyan",
            "keyboard": "green",
            "scroll": "yellow",
            "app_switcher": "magenta",
            "browser_tabs": "blue",
            "code_typing": "bright_white",
        },
        "status_on": "bold green",
        "status_off": "dim red",
        "status_paused": "bold yellow",
        "footer_style": "dim",
        "flash_style": "bold green",
        "app_background": "#0d1117",
    },
    "hacker": {
        "header_style": "bold green",
        "panel_border": "green",
        "title_style": "bold bright_green",
        "sim_colors": {
            "mouse": "bright_green",
            "keyboard": "green",
            "scroll": "dark_green",
            "app_switcher": "spring_green3",
            "browser_tabs": "sea_green2",
            "code_typing": "bright_white",
        },
        "status_on": "bold bright_green",
        "status_off": "dim green",
        "status_paused": "bold yellow",
        "footer_style": "dim green",
        "flash_style": "bold bright_green",
        "app_background": "#001100",
    },
    "warm": {
        "header_style": "bold dark_orange",
        "panel_border": "dark_orange",
        "title_style": "bold gold1",
        "sim_colors": {
            "mouse": "gold1",
            "keyboard": "orange3",
            "scroll": "dark_orange",
            "app_switcher": "indian_red",
            "browser_tabs": "salmon1",
            "code_typing": "bright_white",
        },
        "status_on": "bold gold1",
        "status_off": "dim red",
        "status_paused": "bold orange3",
        "footer_style": "dim",
        "flash_style": "bold gold1",
        "app_background": "#1a0f00",
    },
}

#: Ordered list of available theme names.
THEME_NAMES: list[str] = list(THEMES.keys())
