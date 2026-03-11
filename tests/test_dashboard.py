"""Tests for phantom.ui.dashboard."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

from phantom.config.schema import PhantomConfig
from phantom.core.stats import Stats
from phantom.ui.dashboard import Dashboard, _format_uptime
from phantom.ui.log_handler import DequeHandler


class TestFormatUptime:
    def test_zero(self):
        assert _format_uptime(0) == "00:00:00"

    def test_seconds(self):
        assert _format_uptime(45) == "00:00:45"

    def test_minutes(self):
        assert _format_uptime(125) == "00:02:05"

    def test_hours(self):
        assert _format_uptime(3661) == "01:01:01"

    def test_large(self):
        assert _format_uptime(86400) == "24:00:00"


class TestDashboardBuild:
    def _make_dashboard(self):
        stats = Stats()
        config = PhantomConfig()
        handler = DequeHandler(maxlen=50)
        handler.setFormatter(logging.Formatter("%(message)s"))
        on_toggle = MagicMock(return_value=True)
        on_quit = MagicMock()
        dash = Dashboard(stats, config, handler, on_toggle, on_quit)
        return dash, stats, handler, on_toggle, on_quit

    def test_build_layout_returns_layout(self):
        dash, _, _, _, _ = self._make_dashboard()
        from rich.layout import Layout

        layout = dash._build_layout()
        assert isinstance(layout, Layout)

    def test_build_header_running(self):
        dash, stats, _, _, _ = self._make_dashboard()
        stats.mark_active(True)
        snap = stats.snapshot()
        panel = dash._build_header(snap)
        from rich.panel import Panel

        assert isinstance(panel, Panel)

    def test_build_header_paused(self):
        dash, stats, _, _, _ = self._make_dashboard()
        snap = stats.snapshot()  # active=False by default
        panel = dash._build_header(snap)
        from rich.panel import Panel

        assert isinstance(panel, Panel)

    def test_build_stats_panel_empty(self):
        dash, stats, _, _, _ = self._make_dashboard()
        snap = stats.snapshot()
        panel = dash._build_stats_panel(snap)
        from rich.panel import Panel

        assert isinstance(panel, Panel)

    def test_build_stats_panel_with_actions(self):
        dash, stats, _, _, _ = self._make_dashboard()
        stats.record_action("mouse")
        stats.record_action("mouse")
        stats.record_action("keyboard")
        snap = stats.snapshot()
        panel = dash._build_stats_panel(snap)
        from rich.panel import Panel

        assert isinstance(panel, Panel)

    def test_build_logs_panel_empty(self):
        dash, _, _, _, _ = self._make_dashboard()
        panel = dash._build_logs_panel()
        from rich.panel import Panel

        assert isinstance(panel, Panel)

    def test_build_logs_panel_with_lines(self):
        dash, _, handler, _, _ = self._make_dashboard()
        logger = logging.getLogger("test.dash.logs")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.info("test message")
        panel = dash._build_logs_panel()
        from rich.panel import Panel

        assert isinstance(panel, Panel)
        logger.removeHandler(handler)

    def test_build_footer(self):
        dash, _, _, _, _ = self._make_dashboard()
        panel = dash._build_footer()
        from rich.panel import Panel

        assert isinstance(panel, Panel)


class TestDashboardActions:
    def test_handle_key_quit(self):
        stats = Stats()
        config = PhantomConfig()
        handler = DequeHandler()
        on_toggle = MagicMock(return_value=True)
        on_quit = MagicMock()
        dash = Dashboard(stats, config, handler, on_toggle, on_quit)

        dash.handle_key("q")
        on_quit.assert_called_once()

    def test_handle_key_toggle(self):
        stats = Stats()
        config = PhantomConfig()
        handler = DequeHandler()
        on_toggle = MagicMock(return_value=True)
        on_quit = MagicMock()
        dash = Dashboard(stats, config, handler, on_toggle, on_quit)

        dash.handle_key("s")
        on_toggle.assert_called_once()

    def test_handle_key_uppercase(self):
        stats = Stats()
        config = PhantomConfig()
        handler = DequeHandler()
        on_toggle = MagicMock(return_value=True)
        on_quit = MagicMock()
        dash = Dashboard(stats, config, handler, on_toggle, on_quit)

        dash.handle_key("Q")
        on_quit.assert_called_once()

    def test_handle_key_unknown(self):
        stats = Stats()
        config = PhantomConfig()
        handler = DequeHandler()
        on_toggle = MagicMock(return_value=True)
        on_quit = MagicMock()
        dash = Dashboard(stats, config, handler, on_toggle, on_quit)

        dash.handle_key("x")  # should not crash
        on_toggle.assert_not_called()
        on_quit.assert_not_called()

    def test_stop(self):
        stats = Stats()
        config = PhantomConfig()
        handler = DequeHandler()
        dash = Dashboard(stats, config, handler, MagicMock(), MagicMock())

        dash.stop()
        assert dash._stop_event.is_set()
