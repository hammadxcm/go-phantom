"""Alt+Tab / Cmd+Tab app switching simulation."""

from __future__ import annotations

import random
import time

from pynput.keyboard import Controller, Key

from phantom.config.schema import AppSwitcherConfig
from phantom.core.platform import OS, current_os
from phantom.simulators.base import BaseSimulator


class AppSwitcherSimulator(BaseSimulator):
    """Simulate switching between open applications.

    Uses Alt+Tab on Linux/Windows and Cmd+Tab on macOS to cycle
    through a random number of open application windows.
    """

    def __init__(self) -> None:
        """Initialise the app switcher simulator.

        Sets up a keyboard controller and determines the correct
        modifier key for the current platform.
        """
        super().__init__()
        self._controller = Controller()
        self._modifier = Key.cmd if current_os() == OS.MACOS else Key.alt

    def execute(self, config: AppSwitcherConfig) -> str:
        """Simulate Alt+Tab or Cmd+Tab app switching.

        Args:
            config: App switcher simulator configuration.

        Returns:
            Detail string describing the app switch action.
        """
        tabs = random.randint(config.min_tabs, config.max_tabs)

        self._controller.press(self._modifier)
        try:
            time.sleep(random.uniform(0.05, 0.10))

            for _ in range(tabs):
                self._controller.press(Key.tab)
                try:
                    time.sleep(random.uniform(0.03, 0.08))
                finally:
                    self._controller.release(Key.tab)
                time.sleep(random.uniform(0.15, 0.40))
        finally:
            self._controller.release(self._modifier)

        mod_name = "Cmd" if self._modifier == Key.cmd else "Alt"
        detail = f"App switch {tabs} tabs via {mod_name}+Tab"
        self.log.info(detail)
        return detail
