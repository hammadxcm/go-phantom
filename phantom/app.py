"""Main orchestrator - wires all components together."""

from __future__ import annotations

import logging
import threading

import pyautogui

from phantom.config.manager import ConfigManager
from phantom.core.platform import check_platform_requirements
from phantom.core.scheduler import Scheduler
from phantom.core.stats import Stats
from phantom.hotkeys.manager import HotkeyManager
from phantom.simulators.app_switcher import AppSwitcherSimulator
from phantom.simulators.base import BaseSimulator
from phantom.simulators.browser_tabs import BrowserTabsSimulator
from phantom.simulators.keyboard import KeyboardSimulator
from phantom.simulators.mouse import MouseSimulator
from phantom.simulators.scroll import ScrollSimulator
from phantom.stealth.process import mask_process_name
from phantom.ui.tray import TrayIcon

log = logging.getLogger(__name__)

# ─── Visual status banners ────────────────────────────────────────────────────
_GREEN = "\033[0;32m"
_RED = "\033[0;31m"
_YELLOW = "\033[1;33m"
_CYAN = "\033[0;36m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"


def _print_status(state: str) -> None:
    """Print a visible status banner to the console."""
    import sys as _sys

    if state == "on":
        print(f"\n{_GREEN}{_BOLD}  ▶ Phantom ON  — Simulation running{_RESET}")
        print(f"{_DIM}    Ctrl+Alt+S to pause  |  Ctrl+Alt+Q to quit{_RESET}\n")
    elif state == "off":
        print(f"\n{_YELLOW}{_BOLD}  ⏸ Phantom PAUSED  — Simulation stopped{_RESET}")
        print(f"{_DIM}    Ctrl+Alt+S to resume  |  Ctrl+Alt+Q to quit{_RESET}\n")
    elif state == "quit":
        print(f"\n{_RED}{_BOLD}  ■ Phantom OFF  — Shutting down{_RESET}\n")
    _sys.stdout.flush()


class PhantomApp:
    """Application entry point. Wires config, simulators, scheduler, UI, and hotkeys."""

    def __init__(
        self,
        config_path: str | None = None,
        cli_overrides: dict | None = None,
    ) -> None:
        self._config_mgr = ConfigManager(config_path)
        if cli_overrides:
            self._apply_overrides(cli_overrides)
        self._config_lock = threading.Lock()
        self._stats = Stats()
        self._simulators = self._create_simulators()
        self._scheduler = Scheduler(
            config=self._config_mgr.config,
            simulators=self._simulators,
            config_lock=self._config_lock,
            stats=self._stats,
        )
        self._tray = TrayIcon(
            on_toggle=self._handle_toggle,
            on_quit=self._handle_quit,
            on_hide=self._handle_hide,
        )
        self._hotkey_mgr = HotkeyManager(
            config=self._config_mgr.config.hotkeys,
            on_toggle=self._handle_hotkey_toggle,
            on_quit=self._handle_quit,
            on_hide=self._handle_hide,
        )
        self._dashboard = None

    def run(self, tui: bool = False, log_handler=None) -> None:
        """Start all components. Blocks on tray or TUI event loop (main thread)."""
        # Disable pyautogui failsafe (corner abort)
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0

        # Platform checks
        check_platform_requirements()

        # Stealth: rename process
        cfg = self._config_mgr.config
        if cfg.stealth.rename_process:
            mask_process_name(cfg.stealth.process_name)

        # Start hotkey listener (daemon thread)
        self._hotkey_mgr.start()

        # Auto-start scheduler
        self._scheduler.start()

        if tui and log_handler is not None:
            from phantom.ui.dashboard import Dashboard

            self._dashboard = Dashboard(
                stats=self._stats,
                config=cfg,
                log_handler=log_handler,
                on_toggle=self._handle_toggle,
                on_quit=self._handle_quit,
            )
            log.info("Phantom started (TUI mode). Press %s to toggle.", cfg.hotkeys.toggle)
            self._dashboard.run()
        else:
            self._tray.update_status(True)
            log.info("Phantom started. Press %s to toggle.", cfg.hotkeys.toggle)
            _print_status("on")
            # Run tray on main thread (required on macOS)
            self._tray.run()

    def _handle_toggle(self) -> bool:
        """Toggle scheduler, return new active state."""
        active = self._scheduler.toggle()
        log.info("Simulation %s", "started" if active else "paused")
        _print_status("on" if active else "off")
        return active

    def _handle_hotkey_toggle(self) -> None:
        """Handle toggle from hotkey (no return value needed)."""
        active = self._handle_toggle()
        self._tray.update_status(active)

    def _handle_quit(self) -> None:
        log.info("Quitting Phantom")
        _print_status("quit")
        self._scheduler.shutdown()
        self._hotkey_mgr.stop()
        self._tray.stop()

    def _handle_hide(self) -> None:
        cfg = self._config_mgr.config
        if cfg.stealth.hide_tray:
            self._tray.show()
            with self._config_lock:
                cfg.stealth.hide_tray = False
        else:
            self._tray.hide()
            with self._config_lock:
                cfg.stealth.hide_tray = True

    def _apply_overrides(self, overrides: dict) -> None:
        """Apply CLI overrides to the loaded config."""
        cfg = self._config_mgr.config
        all_sims = {"mouse", "keyboard", "scroll", "app_switcher", "browser_tabs"}

        # Handle --*-only / --only / --all (exclusive selection)
        if "_only" in overrides:
            enabled = overrides.pop("_only")
            for sim in all_sims:
                sub = getattr(cfg, sim)
                sub.enabled = sim in enabled

        # Handle --enable (add to existing)
        if "_enable" in overrides:
            for sim in overrides.pop("_enable"):
                getattr(cfg, sim).enabled = True

        # Handle --disable (remove from existing)
        if "_disable" in overrides:
            for sim in overrides.pop("_disable"):
                getattr(cfg, sim).enabled = False

        # Apply section overrides (timing, mouse, keyboard, etc.)
        for section, values in overrides.items():
            if isinstance(values, dict):
                self._config_mgr.update(section, **values)

    @staticmethod
    def _create_simulators() -> dict[str, BaseSimulator]:
        return {
            "mouse": MouseSimulator(),
            "keyboard": KeyboardSimulator(),
            "scroll": ScrollSimulator(),
            "app_switcher": AppSwitcherSimulator(),
            "browser_tabs": BrowserTabsSimulator(),
        }
