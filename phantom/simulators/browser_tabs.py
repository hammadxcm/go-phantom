"""Ctrl+Tab browser tab switching simulation."""

from __future__ import annotations

import random
import time

from pynput.keyboard import Controller, Key

from phantom.config.schema import BrowserTabsConfig
from phantom.simulators.base import BaseSimulator


class BrowserTabsSimulator(BaseSimulator):
    """Simulates switching between browser tabs with Ctrl+Tab."""

    def __init__(self) -> None:
        super().__init__()
        self._controller = Controller()

    def execute(self, config: BrowserTabsConfig) -> None:
        tabs = random.randint(1, 4)

        for _ in range(tabs):
            self._controller.press(Key.ctrl)
            time.sleep(random.uniform(0.02, 0.06))
            self._controller.press(Key.tab)
            time.sleep(random.uniform(0.03, 0.08))
            self._controller.release(Key.tab)
            self._controller.release(Key.ctrl)
            time.sleep(random.uniform(0.20, 0.50))

        self.log.debug("Browser tab switch: %d tabs", tabs)
