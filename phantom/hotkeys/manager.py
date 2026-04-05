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
        on_code_typing: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the hotkey manager.

        Args:
            config: Hotkey configuration with key bindings.
            on_toggle: Callback for the toggle hotkey.
            on_quit: Callback for the quit hotkey.
            on_hide: Callback for the hide-tray hotkey.
            on_code_typing: Optional callback for the code-typing toggle hotkey.
        """
        self._config = config
        self._listener: GlobalHotKeys | None = None

        def _safe(fn: Callable[[], None]) -> Callable[[], None]:
            """Wrap a callback so exceptions don't crash the hotkey listener."""

            def wrapper() -> None:
                try:
                    fn()
                except Exception:
                    log.exception("Hotkey callback failed")

            return wrapper

        hotkey_map: dict[str, Callable] = {
            config.toggle: _safe(on_toggle),
            config.quit: _safe(on_quit),
            config.hide_tray: _safe(on_hide),
        }
        if on_code_typing:
            hotkey_map[config.code_typing] = _safe(on_code_typing)
        self._listener = GlobalHotKeys(hotkey_map)
        self._listener.daemon = True

    def start(self) -> None:
        """Start listening for global hotkeys."""
        if self._listener:
            self._listener.start()
            log.info(
                "Hotkeys registered: toggle=%s, quit=%s, hide=%s, code_typing=%s",
                self._config.toggle,
                self._config.quit,
                self._config.hide_tray,
                self._config.code_typing,
            )

    def stop(self) -> None:
        """Stop listening for global hotkeys and unregister them."""
        if self._listener:
            self._listener.stop()
            log.info("Hotkeys unregistered")
