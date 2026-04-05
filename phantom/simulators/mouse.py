"""Bezier curve mouse movement with micro-corrections."""

from __future__ import annotations

import math
import random
import time

from phantom.config.schema import MouseConfig
from phantom.core.randomization import Randomizer
from phantom.simulators.base import BaseSimulator


class MouseSimulator(BaseSimulator):
    """Moves the mouse along human-like Bezier curves.

    Generates randomized Bezier paths with micro-corrections to mimic
    natural hand movements. Ensures minimum travel distance and applies
    jitter near the destination.
    """

    def execute(self, config: MouseConfig) -> str:
        """Move the mouse cursor to a random nearby position.

        Args:
            config: Mouse simulator settings including distance bounds
                and Bezier resolution.

        Returns:
            Detail string describing the movement.
        """
        import pyautogui

        screen_w, screen_h = pyautogui.size()
        current_x, current_y = pyautogui.position()
        start_x, start_y = current_x, current_y

        target_x = self._clamp(
            current_x + random.randint(-config.max_distance, config.max_distance),
            0,
            screen_w - 1,
        )
        target_y = self._clamp(
            current_y + random.randint(-config.max_distance, config.max_distance),
            0,
            screen_h - 1,
        )

        # Ensure minimum distance
        dx, dy = target_x - current_x, target_y - current_y
        if abs(dx) + abs(dy) < config.min_distance:
            sign_x = 1 if dx >= 0 else -1
            sign_y = 1 if dy >= 0 else -1
            target_x = self._clamp(current_x + sign_x * config.min_distance, 0, screen_w - 1)
            target_y = self._clamp(current_y + sign_y * config.min_distance, 0, screen_h - 1)

        start = (float(current_x), float(current_y))
        end = (float(target_x), float(target_y))
        path = Randomizer.bezier_path(start, end, steps=config.bezier_steps)

        for x, y in path:
            pyautogui.moveTo(int(x), int(y), _pause=False)
            time.sleep(Randomizer.step_delay())

        # Micro-correction: subtle drift after arriving (like a human settling)
        did_correct = random.random() < 0.3
        if did_correct:
            jitter_x = target_x + random.randint(-2, 2)
            jitter_y = target_y + random.randint(-2, 2)
            jitter_x = self._clamp(jitter_x, 0, screen_w - 1)
            jitter_y = self._clamp(jitter_y, 0, screen_h - 1)
            # Smooth glide to the correction point
            time.sleep(random.uniform(0.08, 0.20))
            correction_steps = 8
            cx, cy = float(target_x), float(target_y)
            dx = (jitter_x - cx) / correction_steps
            dy = (jitter_y - cy) / correction_steps
            for _ in range(correction_steps):
                cx += dx
                cy += dy
                pyautogui.moveTo(int(cx), int(cy), _pause=False)
                time.sleep(random.uniform(0.010, 0.025))

        dist = math.hypot(target_x - start_x, target_y - start_y)
        correction_str = "yes" if did_correct else "no"
        detail = (
            f"Mouse ({start_x},{start_y})->({target_x},{target_y})"
            f" dist={dist:.0f}px correction={correction_str}"
        )
        self.log.info(detail)
        return detail

    @staticmethod
    def _clamp(value: int, lo: int, hi: int) -> int:
        """Constrain a value to the inclusive range ``[lo, hi]``.

        Args:
            value: The number to clamp.
            lo: Minimum allowed value.
            hi: Maximum allowed value.

        Returns:
            The clamped integer.
        """
        return max(lo, min(hi, value))
