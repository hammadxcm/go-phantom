"""Global hotkey registration via pynput."""

from __future__ import annotations

import logging
from collections.abc import Callable

from pynput.keyboard import GlobalHotKeys

from phantom.config.schema import HotkeyConfig

log = logging.getLogger(__name__)


def _patch_global_hotkeys() -> None:
    """Fix pynput GlobalHotKeys bug where _on_press is called without 'injected' arg.

    Some pynput code paths (notably the Darwin special-keys handler) call
    on_press(key) without the injected parameter, but GlobalHotKeys._on_press
    requires it. This patch makes the injected parameter optional.
    """
    _original = GlobalHotKeys._on_press

    def _patched_on_press(self, key, injected=False):
        return _original(self, key, injected)

    GlobalHotKeys._on_press = _patched_on_press


_patch_global_hotkeys()


class HotkeyManager:
    """Registers and manages global hotkeys using pynput."""

    def __init__(
        self,
        config: HotkeyConfig,
        on_toggle: Callable[[], None],
        on_quit: Callable[[], None],
        on_hide: Callable[[], None],
    ) -> None:
        self._config = config
        self._listener: GlobalHotKeys | None = None
        hotkey_map: dict[str, Callable] = {
            config.toggle: on_toggle,
            config.quit: on_quit,
            config.hide_tray: on_hide,
        }
        self._listener = GlobalHotKeys(hotkey_map)
        self._listener.daemon = True

    def start(self) -> None:
        if self._listener:
            self._listener.start()
            log.info(
                "Hotkeys registered: toggle=%s, quit=%s, hide=%s",
                self._config.toggle,
                self._config.quit,
                self._config.hide_tray,
            )

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            log.info("Hotkeys unregistered")
