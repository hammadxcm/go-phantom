"""Vertical and horizontal scroll simulation."""

from __future__ import annotations

import random
import time

import pyautogui

from phantom.config.schema import ScrollConfig
from phantom.simulators.base import BaseSimulator


class ScrollSimulator(BaseSimulator):
    """Simulates mouse wheel scrolling.

    Produces vertical scrolls with an occasional horizontal scroll
    (10% probability) to emulate natural browsing behavior.
    """

    def execute(self, config: ScrollConfig) -> None:
        """Perform a random scroll sequence.

        Args:
            config: Scroll simulator settings including click range.
        """
        clicks = random.randint(config.min_clicks, config.max_clicks)
        direction = random.choice([-1, 1])  # up or down

        for _ in range(clicks):
            amount = direction * random.randint(1, 3)
            if random.random() < 0.1:
                # Horizontal scroll (10% chance)
                pyautogui.hscroll(amount, _pause=False)
            else:
                pyautogui.scroll(amount, _pause=False)
            time.sleep(random.uniform(0.05, 0.15))

        self.log.debug("Scroll: %d clicks, direction=%d", clicks, direction)
