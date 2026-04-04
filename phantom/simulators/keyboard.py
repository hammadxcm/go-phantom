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

    def execute(self, config: KeyboardConfig) -> str:
        """Simulate modifier key presses to register keyboard activity.

        Args:
            config: Keyboard simulator configuration.

        Returns:
            Detail string describing which keys were pressed.
        """
        num_presses = random.randint(1, config.max_presses)
        pressed_names: list[str] = []

        for _ in range(num_presses):
            if random.random() < config.capslock_chance:
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
                pressed_names.append("CapsLock")
            else:
                key = random.choice(SAFE_KEYS)
                self._controller.press(key)
                try:
                    time.sleep(random.uniform(0.03, 0.10))
                finally:
                    self._controller.release(key)
                pressed_names.append(key.name.title())

            time.sleep(Randomizer.keystroke_delay())

        keys_desc = ", ".join(pressed_names)
        detail = f"Keyboard {num_presses} presses: {keys_desc}"
        self.log.info(detail)
        return detail
