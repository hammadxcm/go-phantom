"""Textual TUI dashboard for real-time monitoring.

This module provides a Rich/Textual-based terminal UI for the Phantom
activity simulator.  The main class, :class:`PhantomDashboard`, renders
live statistics, per-simulator controls, and a scrolling log pane.  Two
modal screens (:class:`HelpScreen` and :class:`SettingsScreen`) supply
quick-reference key-bindings and a configuration overview respectively.

All mutable access to the shared :class:`~phantom.config.schema.PhantomConfig`
object is guarded by a ``threading.Lock`` to avoid data races between the
scheduler thread and the UI refresh timer.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from typing import ClassVar

from rich.table import Table
from rich.text import Text
from textual.app import App
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import RichLog, Static

from phantom.config.presets import PRESET_NAMES, apply_preset
from phantom.config.schema import PhantomConfig
from phantom.constants import ALL_SIMULATORS
from phantom.core.stats import Stats
from phantom.ui.log_handler import DequeHandler
from phantom.ui.themes import THEME_NAMES, THEMES

_SIM_KEYS = {
    "1": "mouse",
    "2": "keyboard",
    "3": "scroll",
    "4": "app_switcher",
    "5": "browser_tabs",
}


def _format_uptime(seconds: float) -> str:
    """Format seconds into HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _logger_to_sim(logger_name: str) -> str | None:
    """Extract simulator name from logger name like 'phantom.simulators.mouse'."""
    parts = logger_name.split(".")
    if len(parts) >= 3 and parts[1] == "simulators":
        return parts[2]
    return None


def _style_for_log(logger_name: str, level: int, theme: dict) -> str:
    """Return Rich style string based on logger name and level."""
    if level >= logging.ERROR:
        return "bold red"
    if level >= logging.WARNING:
        return "bold yellow"
    sim = _logger_to_sim(logger_name)
    sim_colors = theme["sim_colors"]
    if sim and sim in sim_colors:
        return str(sim_colors[sim])
    return "dim white"


class HelpScreen(ModalScreen):
    """Modal overlay showing key bindings.

    Displays a styled list of all available keyboard shortcuts.  The
    screen is dismissed by pressing ``h`` or ``Escape``.

    Args:
        theme: Theme dictionary containing ``title_style`` and colour
            definitions used to render the key labels.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("h", "dismiss", "Close"),
        Binding("escape", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > Static {
        width: 60;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: solid $accent;
    }
    """

    def __init__(self, theme: dict) -> None:
        super().__init__()
        self._theme = theme

    def compose(self):
        text = Text()
        bindings = [
            ("S", "Toggle all simulators on/off"),
            ("\u2191 / \u2193", "Navigate simulators"),
            ("1-5", "Select sim (2nd press: deselect + toggle enabled)"),
            ("\u2190 / \u2192", "Adjust selected weight or interval speed"),
            ("+ / =", "Increase weight (+5) or decrease interval (faster)"),
            ("-", "Decrease weight (-5) or increase interval (slower)"),
            ("Space", "Pause/resume selected simulator"),
            ("P", "Cycle through preset profiles"),
            ("T", "Cycle color theme"),
            ("W", "Save current config to disk"),
            ("C", "Show/hide settings overlay"),
            ("H", "Show/hide this help"),
            ("Q", "Quit Phantom"),
        ]
        for key, desc in bindings:
            text.append(f"  {key:<8}", style=self._theme["title_style"])
            text.append(f"{desc}\n", style="white")
        yield Static(text, id="help-content")


class SettingsScreen(ModalScreen):
    """Modal overlay showing current configuration.

    Renders a read-only snapshot of timing, simulator, stealth, hotkey,
    and profile settings.  Dismissed by pressing ``c`` or ``Escape``.

    Args:
        config: The current Phantom configuration object.
        theme: Active theme dictionary for styling.
        paused_sims: Set of simulator names that are currently paused.
        preset_name: Name of the active preset, or ``None``.
        theme_name: Human-readable name of the active colour theme.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("c", "dismiss", "Close"),
        Binding("escape", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
    }
    SettingsScreen > Static {
        width: 70;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: solid $accent;
    }
    """

    def __init__(self, config: PhantomConfig, theme: dict, paused_sims: set,
                 preset_name: str | None, theme_name: str) -> None:
        super().__init__()
        self._config = config
        self._theme = theme
        self._paused_sims = paused_sims
        self._preset_name = preset_name
        self._theme_name = theme_name

    def compose(self):
        text = Text()
        text.append("  Timing\n", style=self._theme["title_style"])
        text.append(f"    Interval mean:   {self._config.timing.interval_mean:.1f}s\n")
        text.append(f"    Interval stddev: {self._config.timing.interval_stddev:.1f}s\n")
        text.append(f"    Idle chance:     {self._config.timing.idle_chance:.0%}\n\n")

        text.append("  Simulators\n", style=self._theme["title_style"])
        sim_colors = self._theme["sim_colors"]
        for sim_name in ALL_SIMULATORS:
            sim_cfg = getattr(self._config, sim_name)
            color = sim_colors.get(sim_name, "white")
            enabled_str = "ON" if sim_cfg.enabled else "OFF"
            paused_str = " [PAUSED]" if sim_name in self._paused_sims else ""
            label = sim_name.replace("_", " ").title()
            text.append(f"    {label:<16}", style=color)
            text.append(f"  {enabled_str:<4}  w={sim_cfg.weight:.0f}{paused_str}\n")

        text.append("\n  Stealth\n", style=self._theme["title_style"])
        text.append(f"    Rename process:  {self._config.stealth.rename_process}\n")
        text.append(f"    Process name:    {self._config.stealth.process_name}\n")
        text.append(f"    Hide tray:       {self._config.stealth.hide_tray}\n\n")

        text.append("  Hotkeys\n", style=self._theme["title_style"])
        text.append(f"    Toggle:  {self._config.hotkeys.toggle}\n")
        text.append(f"    Quit:    {self._config.hotkeys.quit}\n")
        text.append(f"    Hide:    {self._config.hotkeys.hide_tray}\n\n")

        text.append("  Profile\n", style=self._theme["title_style"])
        text.append(f"    Preset:  {self._preset_name or 'none'}\n")
        text.append(f"    Theme:   {self._theme_name}\n")

        yield Static(text, id="settings-content")


class PhantomDashboard(App):
    """Textual TUI dashboard showing real-time stats and live logs.

    The dashboard refreshes every 250 ms, reading a stats snapshot and
    rendering header, stats table, preview, footer, and log widgets.
    All reads of the shared ``PhantomConfig`` are performed under
    ``self._config_lock`` to avoid torn reads from the scheduler thread.

    Args:
        stats: Shared statistics accumulator.
        config: Mutable configuration object (shared with scheduler).
        log_handler: :class:`DequeHandler` that collects log records for
            display in the scrolling log pane.
        on_toggle: Callback invoked when the user presses ``S`` to toggle
            all simulators.
        on_quit: Callback invoked on quit (``Q``).
        on_sim_toggle: Optional callback for toggling a single simulator.
        on_save_config: Optional callback to persist config to disk.
        on_sim_pause: Optional callback to pause/resume a single simulator.
        config_lock: Lock guarding ``config`` mutations.  A new lock is
            created if ``None``.
        preset_name: Name of the initially active preset, if any.
    """

    CSS = """
    #header {
        height: 1;
        dock: top;
    }
    #footer {
        height: 1;
        dock: bottom;
    }
    #body {
        height: 1fr;
    }
    #left {
        width: 1fr;
        min-width: 30;
    }
    #stats {
        height: auto;
        max-height: 70%;
    }
    #preview {
        height: auto;
        min-height: 3;
    }
    #logs {
        width: 1fr;
        min-width: 20;
        border-left: solid $accent;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit_phantom", "Quit"),
        Binding("s", "toggle_all", "Toggle"),
        Binding("1", "sim_select('1')", "Sim 1", show=False),
        Binding("2", "sim_select('2')", "Sim 2", show=False),
        Binding("3", "sim_select('3')", "Sim 3", show=False),
        Binding("4", "sim_select('4')", "Sim 4", show=False),
        Binding("5", "sim_select('5')", "Sim 5", show=False),
        Binding("up", "arrow_up", "Up", show=False),
        Binding("down", "arrow_down", "Down", show=False),
        Binding("left", "speed_down", "Speed-", show=False),
        Binding("right", "speed_up", "Speed+", show=False),
        Binding("plus,equals_sign", "speed_up", "Speed+", show=False),
        Binding("minus", "speed_down", "Speed-", show=False),
        Binding("space", "pause_sim", "Pause", show=False),
        Binding("p", "cycle_preset", "Preset"),
        Binding("t", "cycle_theme", "Theme"),
        Binding("w", "save_config", "Save"),
        Binding("c", "toggle_settings", "Config"),
        Binding("h", "toggle_help", "Help"),
    ]

    def __init__(
        self,
        stats: Stats,
        config: PhantomConfig,
        log_handler: DequeHandler,
        on_toggle: Callable[[], bool],
        on_quit: Callable[[], None],
        on_sim_toggle: Callable[[str], None] | None = None,
        on_save_config: Callable[[], None] | None = None,
        on_sim_pause: Callable[[str], bool] | None = None,
        config_lock: threading.Lock | None = None,
        preset_name: str | None = None,
    ) -> None:
        super().__init__()
        self._stats = stats
        self._config = config
        self._log_handler = log_handler
        self._on_toggle = on_toggle
        self._on_quit = on_quit
        self._on_sim_toggle = on_sim_toggle
        self._on_save_config = on_save_config
        self._on_sim_pause = on_sim_pause
        self._config_lock = config_lock or threading.Lock()
        self._preset_name = preset_name
        self._preset_index = (
            PRESET_NAMES.index(preset_name) if preset_name in PRESET_NAMES else -1
        )
        self._flash_msg: str | None = None
        self._flash_until: float = 0
        self._selected_sim: int | None = None
        self._paused_sims: set[str] = set()
        self._theme_index = 0
        self._theme_name = THEME_NAMES[0]
        self._theme = THEMES[self._theme_name]
        self._log_watermark = 0

    def compose(self):
        yield Static(id="header")
        with Horizontal(id="body"):
            with Vertical(id="left"):
                yield Static(id="stats")
                yield Static(id="preview")
            yield RichLog(id="logs", max_lines=500)
        yield Static(id="footer")

    def on_mount(self) -> None:
        """Start the periodic refresh timer when the app is mounted."""
        self.set_interval(0.25, self._refresh_dashboard)

    def _refresh_dashboard(self) -> None:
        """Periodic callback that refreshes all dashboard widgets."""
        snap = self._stats.snapshot()
        self.query_one("#header", Static).update(self._build_header(snap))
        self.query_one("#stats", Static).update(self._build_stats_table(snap))
        self.query_one("#preview", Static).update(self._build_preview_text())
        self.query_one("#footer", Static).update(self._build_footer())
        self._append_new_logs()

    def _build_header(self, snap: dict) -> Text:
        """Build the top-line header showing run state, sim count, and timing.

        Args:
            snap: A statistics snapshot dict produced by
                :meth:`~phantom.core.stats.Stats.snapshot`.

        Returns:
            A Rich :class:`~rich.text.Text` object ready for rendering.
        """
        with self._config_lock:
            enabled = sum(1 for s in ALL_SIMULATORS if getattr(self._config, s).enabled)
            interval_mean = self._config.timing.interval_mean

        active = snap["active"]
        status = Text()
        status.append(" PHANTOM ", style="bold cyan")
        if active:
            status.append(" RUNNING ", style="bold white on green")
        else:
            status.append(" PAUSED ", style="bold white on yellow")

        if self._preset_name:
            status.append(f" [{self._preset_name}]", style="bold magenta")

        status.append(f"  {enabled}/{len(ALL_SIMULATORS)} sims", style="dim")
        status.append(f"  ~{interval_mean:.1f}s", style="dim")
        status.append(
            f"  \u23f1 {_format_uptime(snap['uptime'])}  \u2211{snap['total_actions']}",
            style="dim",
        )
        status.append(f"  [{self._theme_name}]", style="dim")

        if self._flash_msg and time.monotonic() < self._flash_until:
            status.append(f"  {self._flash_msg}", style=self._theme["flash_style"])

        return status

    def _build_stats_table(self, snap: dict) -> Table:
        """Build the simulator status table.

        Args:
            snap: A statistics snapshot dict produced by
                :meth:`~phantom.core.stats.Stats.snapshot`.

        Returns:
            A Rich :class:`~rich.table.Table` with one row per simulator
            showing enabled state, weight, and action count.
        """
        with self._config_lock:
            sim_states = {
                name: (getattr(self._config, name).enabled, getattr(self._config, name).weight)
                for name in ALL_SIMULATORS
            }

        table = Table(show_header=False, box=None, pad_edge=False, show_edge=False)
        table.add_column("", width=1)
        table.add_column("", width=1)
        table.add_column("", width=6)
        table.add_column("", min_width=10)
        table.add_column("", justify="right", width=4)
        table.add_column("", justify="right", width=4)

        sim_colors = self._theme["sim_colors"]
        actions = snap["actions_by_simulator"]
        for i, sim_name in enumerate(ALL_SIMULATORS, 1):
            enabled, weight = sim_states[sim_name]
            paused = sim_name in self._paused_sims
            count = actions.get(sim_name, 0)
            color = sim_colors.get(sim_name, "white")

            selected = self._selected_sim == i
            marker = "\u25b8" if selected else " "
            marker_style = "bold white" if selected else "dim"

            if paused:
                status_text = Text("PAUSE", style=self._theme["status_paused"])
            elif enabled:
                status_text = Text("ON", style=self._theme["status_on"])
            else:
                status_text = Text("OFF", style=self._theme["status_off"])

            name_style = f"{'reverse ' if selected else ''}{color}" if enabled else "dim"
            label = sim_name.replace("_", " ").title()
            table.add_row(
                Text(marker, style=marker_style),
                Text(str(i), style="dim"),
                status_text,
                Text(label, style=name_style),
                Text(f"{weight:.0f}", style=color if enabled else "dim"),
                Text(str(count), style="green" if enabled else "dim"),
            )

        last = snap["last_action_name"]
        if last:
            table.add_row(
                "", "", "", Text("Last", style="dim"),
                "", Text(last.replace("_", " ").title(), style="dim"),
            )

        return table

    def _build_preview_text(self) -> Text:
        entries = self._log_handler.lines_styled
        sim_colors = self._theme["sim_colors"]
        last_per_sim: dict[str, str] = {}

        for msg, logger_name, _level in reversed(entries):
            sim = _logger_to_sim(logger_name)
            if sim and sim in sim_colors and sim not in last_per_sim:
                last_per_sim[sim] = msg
            if len(last_per_sim) == len(ALL_SIMULATORS):
                break

        text = Text()
        if not last_per_sim:
            text.append("(no actions yet)", style="dim")
        else:
            for sim_name in ALL_SIMULATORS:
                if sim_name in last_per_sim:
                    color = sim_colors.get(sim_name, "white")
                    label = sim_name.replace("_", " ").title()
                    msg = last_per_sim[sim_name]
                    parts = msg.split(" ", 1)
                    action_text = parts[1] if len(parts) > 1 else msg
                    text.append(f"  {label}", style=f"bold {color}")
                    text.append(f" \u2192 {action_text}\n", style=color)

        return text

    def _build_footer(self) -> Text:
        t = Text()
        ks = self._theme["title_style"]
        t.append(" S", style=ks)
        t.append(" Toggle ", style="dim")
        t.append("\u2191\u2193", style=ks)
        t.append(" Sims ", style="dim")
        t.append("\u2190\u2192", style=ks)
        t.append(" Speed ", style="dim")
        t.append("Space", style=ks)
        t.append(" Pause ", style="dim")
        t.append("P", style=ks)
        t.append(" Preset ", style="dim")
        t.append("T", style=ks)
        t.append(" Theme ", style="dim")
        t.append("W", style=ks)
        t.append(" Save ", style="dim")
        t.append("C", style=ks)
        t.append(" Config ", style="dim")
        t.append("H", style=ks)
        t.append(" Help ", style="dim")
        t.append("Q", style=ks)
        t.append(" Quit", style="dim")
        return t

    def _append_new_logs(self) -> None:
        entries = self._log_handler.lines_styled
        new_count = len(entries) - self._log_watermark
        if new_count <= 0:
            if len(entries) < self._log_watermark:
                self._log_watermark = len(entries)
            return
        rich_log = self.query_one("#logs", RichLog)
        for msg, logger_name, level in entries[-new_count:]:
            style = _style_for_log(logger_name, level, self._theme)
            rich_log.write(Text(msg, style=style))
        self._log_watermark = len(entries)

    # --- Action methods (bound to BINDINGS) ---

    def action_quit_phantom(self) -> None:
        self._on_quit()
        self.exit()

    def action_toggle_all(self) -> None:
        self._on_toggle()

    def action_sim_select(self, key: str) -> None:
        sim_index = int(key)
        if self._selected_sim == sim_index:
            self._selected_sim = None
            sim_name = _SIM_KEYS[key]
            with self._config_lock:
                sim_cfg = getattr(self._config, sim_name)
                sim_cfg.enabled = not sim_cfg.enabled
            if self._on_sim_toggle:
                self._on_sim_toggle(sim_name)
        else:
            self._selected_sim = sim_index

    def action_arrow_up(self) -> None:
        if self._selected_sim is None:
            self._selected_sim = len(ALL_SIMULATORS)
        else:
            self._selected_sim = (self._selected_sim - 2) % len(ALL_SIMULATORS) + 1

    def action_arrow_down(self) -> None:
        if self._selected_sim is None:
            self._selected_sim = 1
        else:
            self._selected_sim = self._selected_sim % len(ALL_SIMULATORS) + 1

    def action_speed_up(self) -> None:
        if self._selected_sim is not None:
            self._adjust_weight(+5.0)
        else:
            with self._config_lock:
                self._config.timing.interval_mean = max(
                    1.0, self._config.timing.interval_mean - 1.0
                )
            self._flash(f"Interval: {self._config.timing.interval_mean:.1f}s")

    def action_speed_down(self) -> None:
        if self._selected_sim is not None:
            self._adjust_weight(-5.0)
        else:
            with self._config_lock:
                self._config.timing.interval_mean += 1.0
            self._flash(f"Interval: {self._config.timing.interval_mean:.1f}s")

    def _adjust_weight(self, delta: float) -> None:
        assert self._selected_sim is not None
        sim_name = ALL_SIMULATORS[self._selected_sim - 1]
        with self._config_lock:
            sim_cfg = getattr(self._config, sim_name)
            sim_cfg.weight = max(1.0, min(100.0, sim_cfg.weight + delta))
        self._flash(f"{sim_name.replace('_', ' ').title()} weight: {sim_cfg.weight:.0f}")

    def action_pause_sim(self) -> None:
        if self._selected_sim is not None and self._on_sim_pause:
            sim_name = ALL_SIMULATORS[self._selected_sim - 1]
            paused = self._on_sim_pause(sim_name)
            if paused:
                self._paused_sims.add(sim_name)
            else:
                self._paused_sims.discard(sim_name)
            state = "paused" if paused else "resumed"
            self._flash(f"{sim_name.replace('_', ' ').title()} {state}")

    def action_cycle_preset(self) -> None:
        self._preset_index = (self._preset_index + 1) % len(PRESET_NAMES)
        name = PRESET_NAMES[self._preset_index]
        with self._config_lock:
            apply_preset(self._config, name)
        self._preset_name = name
        self._flash(f"Preset: {name}")

    def action_cycle_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(THEME_NAMES)
        self._theme_name = THEME_NAMES[self._theme_index]
        self._theme = THEMES[self._theme_name]
        self._flash(f"Theme: {self._theme_name}")

    def action_save_config(self) -> None:
        if self._on_save_config:
            self._on_save_config()
            self._flash("Config saved!")

    def action_toggle_settings(self) -> None:
        self.push_screen(
            SettingsScreen(
                self._config, self._theme, self._paused_sims,
                self._preset_name, self._theme_name,
            )
        )

    def action_toggle_help(self) -> None:
        self.push_screen(HelpScreen(self._theme))

    def _flash(self, msg: str) -> None:
        self._flash_msg = msg
        self._flash_until = time.monotonic() + 2.0

    # --- Compatibility API ---

    def handle_key(self, key: str) -> None:
        """Handle a keypress programmatically (for hotkey listener compat)."""
        action_map = {
            "q": self.action_quit_phantom,
            "s": self.action_toggle_all,
            "+": self.action_speed_up,
            "=": self.action_speed_up,
            "-": self.action_speed_down,
            " ": self.action_pause_sim,
            "w": self.action_save_config,
            "p": self.action_cycle_preset,
            "t": self.action_cycle_theme,
            "c": self.action_toggle_settings,
            "h": self.action_toggle_help,
            "UP": self.action_arrow_up,
            "DOWN": self.action_arrow_down,
            "RIGHT": self.action_speed_up,
            "LEFT": self.action_speed_down,
        }
        if key in _SIM_KEYS:
            self.action_sim_select(key)
            return
        handler = action_map.get(key) or action_map.get(key.lower())
        if handler:
            handler()

    def stop(self) -> None:
        """Signal the dashboard to exit."""
        self.exit()


# Backward-compatible alias
Dashboard = PhantomDashboard
