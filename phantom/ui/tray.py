"""System tray icon and menu."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pystray
from pystray import MenuItem

from phantom.ui.icons import create_status_icon

log = logging.getLogger(__name__)


class TrayIcon:
    """Manages the system tray icon and context menu.

    Provides Start/Pause, Hide, and Quit menu items and updates
    the icon image to reflect the current scheduler state.
    """

    def __init__(
        self,
        on_toggle: Callable[[], bool],
        on_quit: Callable[[], None],
        on_hide: Callable[[], None],
    ) -> None:
        """Initialize the tray icon.

        Args:
            on_toggle: Callback returning ``True`` if now active.
            on_quit: Callback invoked when the user selects Quit.
            on_hide: Callback invoked when the user hides the tray.
        """
        self._on_toggle = on_toggle
        self._on_quit = on_quit
        self._on_hide = on_hide
        self._active = False
        self._icon: pystray.Icon | None = None

    def run(self) -> None:
        """Create and run the tray icon. Blocks on the main thread."""
        self._icon = pystray.Icon(
            name="Phantom",
            icon=create_status_icon(self._active),
            title="Phantom - Paused",
            menu=self._build_menu(),
        )
        log.info("Tray icon starting")
        self._icon.run()

    def stop(self) -> None:
        """Stop and remove the tray icon."""
        if self._icon:
            self._icon.stop()

    def update_status(self, active: bool) -> None:
        """Update the tray icon and tooltip to reflect scheduler state.

        Args:
            active: ``True`` if the scheduler is running.
        """
        self._active = active
        if self._icon:
            self._icon.icon = create_status_icon(active)
            self._icon.title = f"Phantom - {'Active' if active else 'Paused'}"
            self._icon.update_menu()

    def hide(self) -> None:
        """Hide the tray icon without stopping it."""
        if self._icon:
            self._icon.visible = False
            log.info("Tray icon hidden")

    def show(self) -> None:
        """Make the tray icon visible again."""
        if self._icon:
            self._icon.visible = True
            log.info("Tray icon shown")

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            MenuItem(
                lambda _: "Pause" if self._active else "Start",
                self._handle_toggle,
            ),
            pystray.Menu.SEPARATOR,
            MenuItem("Hide Tray", self._handle_hide),
            MenuItem("Quit", self._handle_quit),
        )

    def _handle_toggle(self, icon: pystray.Icon, item: MenuItem) -> None:
        active = self._on_toggle()
        self.update_status(active)

    def _handle_hide(self, icon: pystray.Icon, item: MenuItem) -> None:
        self._on_hide()

    def _handle_quit(self, icon: pystray.Icon, item: MenuItem) -> None:
        self._on_quit()
