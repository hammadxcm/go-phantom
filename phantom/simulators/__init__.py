"""Activity simulators."""

from __future__ import annotations

from phantom.simulators.app_switcher import AppSwitcherSimulator
from phantom.simulators.base import BaseSimulator
from phantom.simulators.browser_tabs import BrowserTabsSimulator
from phantom.simulators.keyboard import KeyboardSimulator
from phantom.simulators.mouse import MouseSimulator
from phantom.simulators.scroll import ScrollSimulator

__all__ = [
    "SIMULATOR_REGISTRY",
    "AppSwitcherSimulator",
    "BaseSimulator",
    "BrowserTabsSimulator",
    "KeyboardSimulator",
    "MouseSimulator",
    "ScrollSimulator",
    "create_simulators",
]

# ─── Simulator registry ──────────────────────────────────────────────────────
# Maps simulator name → class. Third-party or custom simulators can register
# themselves via register_simulator() at import time.

SIMULATOR_REGISTRY: dict[str, type[BaseSimulator]] = {
    "mouse": MouseSimulator,
    "keyboard": KeyboardSimulator,
    "scroll": ScrollSimulator,
    "app_switcher": AppSwitcherSimulator,
    "browser_tabs": BrowserTabsSimulator,
}


def register_simulator(name: str, cls: type[BaseSimulator]) -> None:
    """Register a custom simulator class under a given name.

    Args:
        name: Key to store the simulator under in ``SIMULATOR_REGISTRY``.
        cls: A :class:`BaseSimulator` subclass to associate with *name*.

    Raises:
        TypeError: If *cls* is not a subclass of :class:`BaseSimulator`.
    """
    if not issubclass(cls, BaseSimulator):
        raise TypeError(f"{cls!r} must be a subclass of BaseSimulator")
    SIMULATOR_REGISTRY[name] = cls


def create_simulators() -> dict[str, BaseSimulator]:
    """Instantiate all registered simulators.

    Returns:
        A dictionary mapping simulator names to their instantiated objects.
    """
    return {name: cls() for name, cls in SIMULATOR_REGISTRY.items()}
