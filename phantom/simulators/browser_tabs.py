"""Context-aware browser tab switching simulation."""

from __future__ import annotations

import random
import time

from pynput.keyboard import Controller, Key

from phantom.config.schema import BrowserTabsConfig
from phantom.core.active_window import get_active_window
from phantom.core.platform import current_os
from phantom.core.tab_shortcuts import TabShortcut, lookup_shortcut
from phantom.simulators.base import BaseSimulator


class BrowserTabsSimulator(BaseSimulator):
    """Simulates switching between browser tabs with context-aware shortcuts."""

    def __init__(self) -> None:
        """Initialize the simulator with a keyboard controller."""
        super().__init__()
        self._controller = Controller()

    def execute(self, config: BrowserTabsConfig) -> str:
        """Simulate switching between browser tabs.

        Args:
            config: Browser-tabs simulation configuration.

        Returns:
            Detail string describing the tab switch action.
        """
        tabs = random.randint(config.min_tabs, config.max_tabs)
        shortcut: TabShortcut | None = None
        app_name = "unknown"
        direction = "forward"

        if config.context_aware:
            window = get_active_window()
            if window and window.app_name:
                app_name = window.app_name
                shortcut = lookup_shortcut(app_name, current_os())

        if shortcut is not None:
            backward = random.random() < config.backward_chance
            keys = shortcut.backward if backward else shortcut.forward
            direction = "backward" if backward else "forward"
            self._press_shortcut(keys, tabs)
            detail = f"Browser tabs {tabs} {direction} in {app_name}"
        else:
            # Fallback: blind Ctrl+Tab
            for _ in range(tabs):
                self._controller.press(Key.ctrl)
                try:
                    time.sleep(random.uniform(0.02, 0.06))
                    self._controller.press(Key.tab)
                    try:
                        time.sleep(random.uniform(0.03, 0.08))
                    finally:
                        self._controller.release(Key.tab)
                finally:
                    self._controller.release(Key.ctrl)
                time.sleep(random.uniform(0.20, 0.50))
            detail = f"Browser tabs {tabs} via Ctrl+Tab"

        self.log.info(detail)
        return detail

    def _press_shortcut(self, keys: tuple, times: int) -> None:
        """Press a multi-key shortcut, releasing in reverse order.

        Args:
            keys: Sequence of keys to press.
            times: Number of times to repeat the shortcut.
        """
        for _ in range(times):
            pressed: list = []
            try:
                for k in keys:
                    self._controller.press(k)
                    pressed.append(k)
                    time.sleep(random.uniform(0.02, 0.06))
            finally:
                for k in reversed(pressed):
                    self._controller.release(k)
            time.sleep(random.uniform(0.20, 0.50))
