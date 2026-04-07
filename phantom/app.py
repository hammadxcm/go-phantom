"""Main orchestrator - wires all components together."""

from __future__ import annotations

import atexit
import logging
import signal
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phantom.ui.dashboard import Dashboard

from phantom.config.manager import ConfigManager
from phantom.constants import ALL_SIMULATORS_SET
from phantom.core.platform import check_platform_requirements
from phantom.core.scheduler import Scheduler
from phantom.core.stats import Stats
from phantom.hotkeys.manager import HotkeyManager
from phantom.simulators import create_simulators
from phantom.simulators.base import BaseSimulator
from phantom.stealth.process import mask_process_name
from phantom.ui.ansi import BOLD, DIM, GREEN, RED, RESET, YELLOW
from phantom.ui.modes import OutputMode
from phantom.ui.tray import TrayIcon

log = logging.getLogger(__name__)

_LOGO = r"""
 ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
 ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
 ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
 ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
 ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
"""


def _print_status(state: str) -> None:
    """Print a visible status banner to the console."""
    import sys as _sys

    # sys.stdout is None when running as a PyInstaller GUI app on Windows
    if _sys.stdout is None:
        return

    if state == "on":
        print(f"\n{GREEN}{BOLD}  ▶ Phantom ON  — Simulation running{RESET}")
        print(f"{DIM}    Ctrl+Alt+S to pause  |  Ctrl+Alt+Q to quit{RESET}\n")
    elif state == "off":
        print(f"\n{YELLOW}{BOLD}  ⏸ Phantom PAUSED  — Simulation stopped{RESET}")
        print(f"{DIM}    Ctrl+Alt+S to resume  |  Ctrl+Alt+Q to quit{RESET}\n")
    elif state == "quit":
        print(f"\n{RED}{BOLD}  ■ Phantom OFF  — Shutting down{RESET}\n")
    _sys.stdout.flush()


def _print_logo(config) -> None:
    """Print the ASCII art logo with version and simulator info."""
    import sys as _sys

    # sys.stdout is None when running as a PyInstaller GUI app on Windows
    if _sys.stdout is None:
        return

    try:
        from rich.console import Console
        from rich.text import Text

        import phantom

        console = Console()
        logo_text = Text(_LOGO.strip(), style="bold cyan")
        console.print(logo_text)

        enabled = sum(
            1
            for s in ("mouse", "keyboard", "scroll", "app_switcher", "browser_tabs")
            if getattr(config, s).enabled
        )
        info = Text()
        info.append(f"  v{phantom.__version__}", style="bold white")
        info.append(f"  •  {enabled}/5 simulators active", style="dim")
        info.append(f"  •  ~{config.timing.interval_mean:.1f}s interval", style="dim")
        console.print(info)
        console.print()
    except ImportError:
        print(_LOGO)


class PhantomApp:
    """Main application orchestrator.

    Wires together configuration, simulators, scheduler, UI layer, and
    hotkey management into a single runnable application.

    Attributes:
        _config_mgr: Manages loading, merging, and persisting configuration.
        _scheduler: Drives periodic simulator ticks.
        _tray: System-tray icon for GUI control.
        _hotkey_mgr: Global hotkey listener (toggle / quit / hide).
    """

    def __init__(
        self,
        config_path: str | None = None,
        cli_overrides: dict | None = None,
        preset: str | None = None,
    ) -> None:
        """Initialise PhantomApp and all sub-components.

        Args:
            config_path: Optional path to a TOML/YAML config file.
            cli_overrides: Optional dict of CLI flag overrides to apply on
                top of the loaded configuration.
            preset: Optional preset name to apply before CLI overrides.
        """
        self._config_mgr = ConfigManager(config_path)

        # Apply preset before CLI overrides
        self._preset_name = preset
        if preset:
            from phantom.config.presets import apply_preset

            apply_preset(self._config_mgr.config, preset)

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
            on_code_typing=self._handle_code_typing_toggle,
        )
        self._dashboard: Dashboard | None = None
        self._gui: object | None = None
        self._tail_stop = threading.Event()

    def run(self, mode: OutputMode = OutputMode.TRAY, log_handler=None) -> None:
        """Start all components and block on the chosen event loop.

        Args:
            mode: Output mode determining how the UI is presented
                (tray, TUI, tail, or ghost).
            log_handler: Optional log handler required for TUI mode to
                feed log records into the dashboard.
        """
        # Disable pyautogui failsafe (corner abort)
        import pyautogui

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0

        atexit.register(self._restore_failsafe)
        signal.signal(signal.SIGTERM, lambda *_: self._handle_quit())

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

        if mode == OutputMode.TUI:
            if log_handler is not None:
                from phantom.ui.dashboard import Dashboard

                self._dashboard = Dashboard(
                    stats=self._stats,
                    config=cfg,
                    log_handler=log_handler,
                    on_toggle=self._handle_toggle,
                    on_quit=self._handle_quit,
                    on_sim_toggle=self._handle_sim_toggle,
                    on_save_config=self._handle_save_config,
                    on_sim_pause=self._handle_sim_pause,
                    config_lock=self._config_lock,
                    preset_name=self._preset_name,
                )
                log.info("Phantom started (TUI mode). Press %s to toggle.", cfg.hotkeys.toggle)
                self._dashboard.run()
        elif mode == OutputMode.TAIL:
            self._run_tail_mode(cfg)
        elif mode == OutputMode.GHOST:
            self._run_ghost_mode(cfg)
        elif mode == OutputMode.GUI:
            self._run_gui_mode(cfg)
        else:
            _print_logo(cfg)
            self._tray.update_status(True)
            log.info("Phantom started. Press %s to toggle.", cfg.hotkeys.toggle)
            _print_status("on")
            # Run tray on main thread (required on macOS)
            self._tray.run()

    def _run_tail_mode(self, cfg) -> None:
        """Streaming colored log mode — no panels, just logs."""
        _print_logo(cfg)
        log.info("Phantom started (tail mode). Press Ctrl+C to quit.")
        _print_status("on")
        try:
            self._tail_stop.wait()
        except KeyboardInterrupt:
            self._handle_quit()

    def _run_ghost_mode(self, cfg) -> None:
        """Silent mode — no terminal output, tray icon for GUI control."""
        self._tray.update_status(True)
        log.info("Phantom started (ghost mode). Press %s to toggle.", cfg.hotkeys.toggle)
        # Run tray on main thread (required on macOS)
        self._tray.run()

    def _run_gui_mode(self, cfg) -> None:
        """GUI mode — tkinter window with optional tray icon."""
        import sys

        from phantom.ui.gui import PhantomGUI

        gui = PhantomGUI(
            stats=self._stats,
            config=cfg,
            config_lock=self._config_lock,
            on_toggle=self._handle_toggle,
            on_quit=self._handle_quit,
            on_save_config=self._handle_save_config,
            on_sim_pause=self._handle_sim_pause,
            preset_name=self._preset_name,
        )
        self._gui = gui
        # On Windows, run tray on a background thread (pystray supports this)
        if sys.platform == "win32":

            def _show_gui() -> None:
                gui._root.after(0, gui._root.deiconify)

            self._tray._on_show_window = _show_gui
            threading.Thread(target=self._tray.run, daemon=True).start()
        self._tray.update_status(True)
        log.info("Phantom started (GUI mode).")
        gui.run()  # tkinter mainloop on main thread

    def _handle_toggle(self) -> bool:
        """Toggle the scheduler between running and paused.

        Returns:
            ``True`` if the scheduler is now active, ``False`` if paused.
        """
        active = self._scheduler.toggle()
        log.info("Simulation %s", "started" if active else "paused")
        _print_status("on" if active else "off")
        return active

    def _handle_hotkey_toggle(self) -> None:
        """Handle toggle triggered via global hotkey.

        Delegates to ``_handle_toggle`` and synchronises the tray icon.
        """
        active = self._handle_toggle()
        self._tray.update_status(active)

    def _handle_quit(self) -> None:
        """Shut down all components in safe order."""
        log.info("Quitting Phantom")
        _print_status("quit")
        self._hotkey_mgr.stop()
        self._scheduler.shutdown()
        self._tail_stop.set()
        self._tray.stop()

    def _handle_hide(self) -> None:
        """Toggle tray icon visibility and persist the stealth setting."""
        cfg = self._config_mgr.config
        if cfg.stealth.hide_tray:
            self._tray.show()
            with self._config_lock:
                cfg.stealth.hide_tray = False
        else:
            self._tray.hide()
            with self._config_lock:
                cfg.stealth.hide_tray = True

    def _handle_code_typing_toggle(self) -> None:
        """Toggle code-typing simulator on/off via hotkey."""
        cfg = self._config_mgr.config
        with self._config_lock:
            cfg.code_typing.enabled = not cfg.code_typing.enabled
        state = "enabled" if cfg.code_typing.enabled else "disabled"
        log.info("Code typing %s (hotkey)", state)

    def _handle_sim_toggle(self, sim_name: str) -> None:
        """Handle individual simulator toggle from TUI."""
        cfg = self._config_mgr.config
        enabled = getattr(cfg, sim_name).enabled
        log.info(
            "Simulator %s %s",
            sim_name.replace("_", " ").title(),
            "enabled" if enabled else "disabled",
        )

    def _handle_sim_pause(self, sim_name: str) -> bool:
        """Toggle pause for a single simulator.

        Args:
            sim_name: Internal simulator key (e.g. ``"mouse"``).

        Returns:
            ``True`` if the simulator is now paused.
        """
        return self._scheduler.toggle_sim_pause(sim_name)

    def _handle_save_config(self) -> None:
        """Persist the current in-memory configuration to disk."""
        self._config_mgr.save()

    def _apply_overrides(self, overrides: dict) -> None:
        """Apply CLI flag overrides to the loaded config.

        Args:
            overrides: Dict produced by the CLI parser containing section
                dicts and special ``_only``/``_enable``/``_disable`` keys.
        """
        cfg = self._config_mgr.config

        # Handle --*-only / --only / --all (exclusive selection)
        if "_only" in overrides:
            enabled = overrides.pop("_only")
            for sim in ALL_SIMULATORS_SET:
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
    def _restore_failsafe() -> None:
        """Restore pyautogui failsafe on exit."""
        import pyautogui

        pyautogui.FAILSAFE = True

    @staticmethod
    def _create_simulators() -> dict[str, BaseSimulator]:
        """Instantiate all registered simulators.

        Returns:
            Mapping of simulator name to simulator instance.
        """
        return create_simulators()
