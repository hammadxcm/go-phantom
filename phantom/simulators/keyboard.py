"""Modifier key press simulation (safe -- no visible output).

This module provides a simulator that presses modifier keys (Shift, Ctrl, Alt)
and occasionally toggles CapsLock to generate keyboard activity without
producing any visible character output.
"""

from __future__ import annotations

import random
import time

from pynput.keyboard import Controller, Key

from phantom.config.schema import KeyboardConfig
from phantom.core.randomization import Randomizer
from phantom.simulators.base import BaseSimulator

SAFE_KEYS = [Key.shift, Key.ctrl, Key.alt]
"""list[Key]: Modifier keys that produce no visible output when pressed alone."""


class KeyboardSimulator(BaseSimulator):
    """Presses modifier keys in isolation to register keyboard activity.

    The simulator randomly selects a modifier key from :data:`SAFE_KEYS` and
    holds it for a short, randomised duration before releasing.  Occasionally
    it performs a CapsLock double-tap instead.
    """

    def __init__(self) -> None:
        """Initialise the keyboard simulator with a pynput controller."""
        super().__init__()
        self._controller = Controller()

    def execute(self, config: KeyboardConfig) -> None:
        """Simulate modifier key presses to register keyboard activity.

        Args:
            config: Keyboard simulator configuration.
        """
        num_presses = random.randint(1, config.max_presses)

        for _ in range(num_presses):
            if random.random() < 0.15:
                # CapsLock double-tap (on then off)
                self._controller.press(Key.caps_lock)
                try:
                    time.sleep(random.uniform(0.03, 0.08))
                finally:
                    self._controller.release(Key.caps_lock)
                time.sleep(random.uniform(0.05, 0.12))
                self._controller.press(Key.caps_lock)
                try:
                    time.sleep(random.uniform(0.03, 0.08))
                finally:
                    self._controller.release(Key.caps_lock)
            else:
                key = random.choice(SAFE_KEYS)
                self._controller.press(key)
                try:
                    time.sleep(random.uniform(0.03, 0.10))
                finally:
                    self._controller.release(key)

            time.sleep(Randomizer.keystroke_delay())

        self.log.debug("Keyboard: %d modifier presses", num_presses)
