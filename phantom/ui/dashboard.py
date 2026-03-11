"""Rich TUI dashboard for real-time monitoring."""

from __future__ import annotations

import threading
from collections.abc import Callable

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from phantom.config.schema import PhantomConfig
from phantom.core.stats import Stats
from phantom.ui.log_handler import DequeHandler


def _format_uptime(seconds: float) -> str:
    """Format seconds into HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class Dashboard:
    """Rich TUI dashboard showing real-time stats and live logs."""

    def __init__(
        self,
        stats: Stats,
        config: PhantomConfig,
        log_handler: DequeHandler,
        on_toggle: Callable[[], bool],
        on_quit: Callable[[], None],
    ) -> None:
        self._stats = stats
        self._config = config
        self._log_handler = log_handler
        self._on_toggle = on_toggle
        self._on_quit = on_quit
        self._stop_event = threading.Event()

    def _build_header(self, snap: dict) -> Panel:
        """Build the header panel with status and uptime."""
        active = snap["active"]
        status = Text()
        status.append("  PHANTOM  ", style="bold white")
        if active:
            status.append(" RUNNING ", style="bold green")
        else:
            status.append(" PAUSED ", style="bold yellow")
        status.append(f"        Uptime: {_format_uptime(snap['uptime'])}", style="dim")
        return Panel(status, style="bold blue")

    def _build_stats_panel(self, snap: dict) -> Panel:
        """Build the simulator stats panel."""
        table = Table(show_header=True, header_style="bold cyan", box=None, pad_edge=False)
        table.add_column("Simulator", style="white", min_width=14)
        table.add_column("Count", justify="right", style="green", min_width=6)

        actions = snap["actions_by_simulator"]
        for name, count in sorted(actions.items(), key=lambda x: x[1], reverse=True):
            table.add_row(name.replace("_", " ").title(), str(count))

        table.add_section()
        table.add_row("Total", str(snap["total_actions"]), style="bold")

        if snap["last_action_name"]:
            table.add_row("")
            table.add_row(
                "Last",
                snap["last_action_name"].replace("_", " ").title(),
                style="dim",
            )

        return Panel(table, title="Stats", border_style="blue")

    def _build_logs_panel(self) -> Panel:
        """Build the live logs panel."""
        lines = self._log_handler.lines
        # Show last 20 lines
        recent = lines[-20:] if len(lines) > 20 else lines
        log_text = Text("\n".join(recent) if recent else "(no logs yet)")
        return Panel(log_text, title="Live Logs", border_style="blue")

    def _build_footer(self) -> Panel:
        """Build the keyboard shortcuts footer."""
        text = Text()
        text.append("  [S] ", style="bold cyan")
        text.append("Toggle  ", style="white")
        text.append("[Q] ", style="bold cyan")
        text.append("Quit  ", style="white")
        text.append("[Ctrl+Alt+S] ", style="dim")
        text.append("Hotkey Toggle  ", style="dim")
        text.append("[Ctrl+Alt+Q] ", style="dim")
        text.append("Hotkey Quit", style="dim")
        return Panel(text, style="dim")

    def _build_layout(self) -> Layout:
        """Build the full dashboard layout."""
        snap = self._stats.snapshot()

        layout = Layout()
        layout.split_column(
            Layout(self._build_header(snap), name="header", size=3),
            Layout(name="body"),
            Layout(self._build_footer(), name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(self._build_stats_panel(snap), name="stats", ratio=1),
            Layout(self._build_logs_panel(), name="logs", ratio=2),
        )
        return layout

    def run(self) -> None:
        """Block on main thread, refreshing dashboard every 0.5s."""
        try:
            with Live(self._build_layout(), refresh_per_second=2, screen=True) as live:
                while not self._stop_event.is_set():
                    live.update(self._build_layout())
                    # Check for keyboard input (non-blocking)
                    self._stop_event.wait(timeout=0.5)
        except KeyboardInterrupt:
            self._on_quit()

    def stop(self) -> None:
        """Signal the dashboard to exit."""
        self._stop_event.set()

    def handle_key(self, key: str) -> None:
        """Handle a keypress from the hotkey listener or stdin."""
        if key.lower() == "q":
            self._on_quit()
            self.stop()
        elif key.lower() == "s":
            self._on_toggle()
