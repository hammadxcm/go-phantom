"""Modifier key press simulation (safe - no visible output)."""

from __future__ import annotations

import random
import time

from pynput.keyboard import Controller, Key

from phantom.config.schema import KeyboardConfig
from phantom.core.randomization import Randomizer
from phantom.simulators.base import BaseSimulator

# Modifier keys that produce no visible output when pressed alone
SAFE_KEYS = [Key.shift, Key.ctrl, Key.alt]

# CapsLock toggle: press twice to return to original state
CAPSLOCK_PAIR = (Key.caps_lock, Key.caps_lock)


class KeyboardSimulator(BaseSimulator):
    """Presses modifier keys in isolation to register keyboard activity."""

    def __init__(self) -> None:
        super().__init__()
        self._controller = Controller()

    def execute(self, config: KeyboardConfig) -> None:
        num_presses = random.randint(1, config.max_presses)

        for _ in range(num_presses):
            if random.random() < 0.15:
                # CapsLock double-tap (on then off)
                self._controller.press(Key.caps_lock)
                time.sleep(random.uniform(0.03, 0.08))
                self._controller.release(Key.caps_lock)
                time.sleep(random.uniform(0.05, 0.12))
                self._controller.press(Key.caps_lock)
                time.sleep(random.uniform(0.03, 0.08))
                self._controller.release(Key.caps_lock)
            else:
                key = random.choice(SAFE_KEYS)
                self._controller.press(key)
                time.sleep(random.uniform(0.03, 0.10))
                self._controller.release(key)

            time.sleep(Randomizer.keystroke_delay())

        self.log.debug("Keyboard: %d modifier presses", num_presses)
