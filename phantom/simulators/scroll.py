"""Vertical and horizontal scroll simulation."""

from __future__ import annotations

import random
import time

from phantom.config.schema import ScrollConfig
from phantom.simulators.base import BaseSimulator


class ScrollSimulator(BaseSimulator):
    """Simulates mouse wheel scrolling.

    Produces vertical scrolls with an occasional horizontal scroll
    (10% probability) to emulate natural browsing behavior.
    """

    def execute(self, config: ScrollConfig) -> str:
        """Perform a random scroll sequence.

        Args:
            config: Scroll simulator settings including click range.

        Returns:
            Detail string describing the scroll action.
        """
        import pyautogui

        clicks = random.randint(config.min_clicks, config.max_clicks)
        direction = random.choice([-1, 1])  # up or down
        v_count = 0
        h_count = 0

        for _ in range(clicks):
            amount = direction * random.randint(1, 3)
            if random.random() < config.horizontal_chance:
                pyautogui.hscroll(amount, _pause=False)
                h_count += 1
            else:
                pyautogui.scroll(amount, _pause=False)
                v_count += 1
            time.sleep(random.uniform(0.05, 0.15))

        dir_name = "down" if direction == 1 else "up"
        detail = (
            f"Scroll {clicks} clicks ({v_count} vertical, {h_count} horizontal)"
            f" direction={dir_name}"
        )
        self.log.info(detail)
        return detail
