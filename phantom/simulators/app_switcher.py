"""Alt+Tab / Cmd+Tab app switching simulation."""

from __future__ import annotations

import random
import time

from pynput.keyboard import Controller, Key

from phantom.config.schema import AppSwitcherConfig
from phantom.core.platform import OS, current_os
from phantom.simulators.base import BaseSimulator


class AppSwitcherSimulator(BaseSimulator):
    """Simulates switching between open applications."""

    def __init__(self) -> None:
        super().__init__()
        self._controller = Controller()
        self._modifier = Key.cmd if current_os() == OS.MACOS else Key.alt

    def execute(self, config: AppSwitcherConfig) -> None:
        tabs = random.randint(1, 3)

        self._controller.press(self._modifier)
        time.sleep(random.uniform(0.05, 0.10))

        for _ in range(tabs):
            self._controller.press(Key.tab)
            time.sleep(random.uniform(0.03, 0.08))
            self._controller.release(Key.tab)
            time.sleep(random.uniform(0.15, 0.40))

        self._controller.release(self._modifier)
        self.log.debug("App switch: %d tabs", tabs)
