"""Centralized constants shared across the phantom package.

Defines the canonical list of simulator names used for config
keys, weight maps, and CLI flags.
"""

from __future__ import annotations

ALL_SIMULATORS: list[str] = ["mouse", "keyboard", "scroll", "app_switcher", "browser_tabs"]
ALL_SIMULATORS_SET: frozenset[str] = frozenset(ALL_SIMULATORS)
