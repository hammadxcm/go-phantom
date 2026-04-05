"""Tests for phantom.ui.dashboard."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from rich.table import Table
from rich.text import Text

from phantom.config.schema import PhantomConfig
from phantom.core.stats import Stats
from phantom.ui.dashboard import Dashboard, PhantomDashboard, _format_uptime
from phantom.ui.themes import THEMES


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


class TestDashboardActions:
    def test_action_quit(self, dashboard):
        dashboard.action_quit_phantom()
        dashboard._on_quit.assert_called_once()

    def test_action_toggle(self, dashboard):
        dashboard.action_toggle_all()
        dashboard._on_toggle.assert_called_once()

    def test_handle_key_quit(self, dashboard):
        dashboard.handle_key("q")
        dashboard._on_quit.assert_called_once()

    def test_handle_key_toggle(self, dashboard):
        dashboard.handle_key("s")
        dashboard._on_toggle.assert_called_once()

    def test_handle_key_uppercase(self, dashboard):
        dashboard.handle_key("Q")
        dashboard._on_quit.assert_called_once()

    def test_handle_key_unknown(self, dashboard):
        dashboard.handle_key("x")
        dashboard._on_toggle.assert_not_called()
        dashboard._on_quit.assert_not_called()

    def test_stop_calls_exit(self, dashboard, monkeypatch):
        exit_mock = MagicMock()
        monkeypatch.setattr(dashboard, "exit", exit_mock)
        dashboard.stop()
        exit_mock.assert_called_once()

    def test_sim_select_and_deselect_toggle(self, log_handler):
        on_sim_toggle = MagicMock()
        dash = Dashboard(
            stats=Stats(),
            config=PhantomConfig(),
            log_handler=log_handler,
            on_toggle=MagicMock(),
            on_quit=MagicMock(),
            on_sim_toggle=on_sim_toggle,
        )

        dash.action_sim_select("1")
        assert dash._selected_sim == 1
        on_sim_toggle.assert_not_called()

        dash.action_sim_select("1")
        assert dash._selected_sim is None
        on_sim_toggle.assert_called_once_with("mouse")

    def test_weight_adjust_selected_sim(self, dashboard):
        dashboard.action_sim_select("1")
        original_weight = dashboard._config.mouse.weight
        dashboard.action_speed_up()
        assert dashboard._config.mouse.weight == original_weight + 5.0

        dashboard.action_speed_down()
        assert dashboard._config.mouse.weight == original_weight

    def test_weight_adjust_no_selection_changes_interval(self, dashboard):
        original = dashboard._config.timing.interval_mean
        dashboard.action_speed_up()
        assert dashboard._config.timing.interval_mean == original - 1.0

    def test_space_pauses_selected_sim(self, log_handler):
        on_sim_pause = MagicMock(return_value=True)
        dash = Dashboard(
            stats=Stats(),
            config=PhantomConfig(),
            log_handler=log_handler,
            on_toggle=MagicMock(),
            on_quit=MagicMock(),
            on_sim_pause=on_sim_pause,
        )

        dash.action_sim_select("1")
        dash.action_pause_sim()
        on_sim_pause.assert_called_once_with("mouse")
        assert "mouse" in dash._paused_sims

    def test_theme_cycle(self, dashboard):
        assert dashboard._theme_name == "default"
        dashboard.action_cycle_theme()
        assert dashboard._theme_name == "hacker"
        dashboard.action_cycle_theme()
        assert dashboard._theme_name == "warm"
        dashboard.action_cycle_theme()
        assert dashboard._theme_name == "default"

    def test_preset_cycle(self, dashboard):
        dashboard.action_cycle_preset()
        assert dashboard._preset_name is not None

    def test_save_config(self, log_handler):
        on_save = MagicMock()
        dash = Dashboard(
            stats=Stats(),
            config=PhantomConfig(),
            log_handler=log_handler,
            on_toggle=MagicMock(),
            on_quit=MagicMock(),
            on_save_config=on_save,
        )
        dash.action_save_config()
        on_save.assert_called_once()

    def test_flash_message(self, dashboard):
        dashboard._flash("test msg")
        assert dashboard._flash_msg == "test msg"
        assert dashboard._flash_until > 0


class TestArrowKeyNavigation:
    def test_arrow_down_selects_first(self, dashboard):
        assert dashboard._selected_sim is None
        dashboard.action_arrow_down()
        assert dashboard._selected_sim == 1

    def test_arrow_down_wraps(self, dashboard):
        dashboard._selected_sim = 6
        dashboard.action_arrow_down()
        assert dashboard._selected_sim == 1

    def test_arrow_up_selects_last(self, dashboard):
        assert dashboard._selected_sim is None
        dashboard.action_arrow_up()
        assert dashboard._selected_sim == 6

    def test_arrow_up_wraps(self, dashboard):
        dashboard._selected_sim = 1
        dashboard.action_arrow_up()
        assert dashboard._selected_sim == 6

    def test_arrow_up_down_cycle(self, dashboard):
        dashboard.action_arrow_down()  # 1
        dashboard.action_arrow_down()  # 2
        dashboard.action_arrow_down()  # 3
        assert dashboard._selected_sim == 3
        dashboard.action_arrow_up()  # 2
        assert dashboard._selected_sim == 2

    def test_arrow_right_via_handle_key(self, dashboard):
        dashboard.action_arrow_down()
        original = dashboard._config.mouse.weight
        dashboard.handle_key("RIGHT")
        assert dashboard._config.mouse.weight == original + 5.0

    def test_arrow_left_via_handle_key(self, dashboard):
        dashboard.action_arrow_down()
        original = dashboard._config.mouse.weight
        dashboard.handle_key("LEFT")
        assert dashboard._config.mouse.weight == max(1.0, original - 5.0)


class TestBuildMethods:
    def test_build_header_running(self, dashboard):
        dashboard._stats.mark_active(True)
        snap = dashboard._stats.snapshot()
        result = dashboard._build_header(snap)
        assert isinstance(result, Text)

    def test_build_header_paused(self, dashboard):
        snap = dashboard._stats.snapshot()
        result = dashboard._build_header(snap)
        assert isinstance(result, Text)

    def test_build_stats_table(self, dashboard):
        snap = dashboard._stats.snapshot()
        result = dashboard._build_stats_table(snap)
        assert isinstance(result, Table)

    def test_build_stats_with_actions(self, dashboard):
        dashboard._stats.record_action("mouse")
        dashboard._stats.record_action("keyboard")
        snap = dashboard._stats.snapshot()
        result = dashboard._build_stats_table(snap)
        assert isinstance(result, Table)

    def test_build_preview_text_empty(self, dashboard):
        snap = dashboard._stats.snapshot()
        result = dashboard._build_preview_text(snap)
        assert isinstance(result, Text)

    def test_build_preview_text_with_details(self, dashboard):
        dashboard._stats.record_action("mouse", "Mouse (0,0)->(100,100) dist=141px correction=no")
        snap = dashboard._stats.snapshot()
        result = dashboard._build_preview_text(snap)
        assert isinstance(result, Text)
        assert "Mouse" in result.plain

    def test_build_footer(self, dashboard):
        result = dashboard._build_footer()
        assert isinstance(result, Text)


class TestThemes:
    def test_all_themes_have_required_keys(self):
        required = {
            "header_style",
            "panel_border",
            "title_style",
            "sim_colors",
            "status_on",
            "status_off",
            "status_paused",
            "footer_style",
            "flash_style",
            "app_background",
        }
        for name, theme in THEMES.items():
            assert required <= set(theme.keys()), f"Theme {name!r} missing keys"

    def test_all_themes_have_sim_colors(self):
        sims = {"mouse", "keyboard", "scroll", "app_switcher", "browser_tabs", "code_typing"}
        for name, theme in THEMES.items():
            assert sims <= set(theme["sim_colors"].keys()), f"Theme {name!r} missing sim colors"


class TestBackwardCompat:
    def test_alias_exists(self):
        assert Dashboard is PhantomDashboard


@pytest.mark.asyncio
class TestTUIIntegration:
    async def test_tui_renders(self, default_config, log_handler):
        from textual.widgets import RichLog, Static

        app = PhantomDashboard(
            stats=Stats(),
            config=default_config,
            log_handler=log_handler,
            on_toggle=MagicMock(return_value=True),
            on_quit=MagicMock(),
        )
        async with app.run_test():
            assert app.query_one("#header", Static)
            assert app.query_one("#stats", Static)
            assert app.query_one("#logs", RichLog)
            assert app.query_one("#footer", Static)
            assert app.query_one("#preview", Static)

    async def test_key_press_quit(self, default_config, log_handler):
        on_quit = MagicMock()
        app = PhantomDashboard(
            stats=Stats(),
            config=default_config,
            log_handler=log_handler,
            on_toggle=MagicMock(return_value=True),
            on_quit=on_quit,
        )
        async with app.run_test() as pilot:
            await pilot.press("q")
            on_quit.assert_called_once()

    async def test_help_screen_opens(self, default_config, log_handler):
        from phantom.ui.dashboard import HelpScreen

        app = PhantomDashboard(
            stats=Stats(),
            config=default_config,
            log_handler=log_handler,
            on_toggle=MagicMock(return_value=True),
            on_quit=MagicMock(),
        )
        async with app.run_test() as pilot:
            await pilot.press("h")
            assert isinstance(app.screen, HelpScreen)

    async def test_settings_screen_opens(self, default_config, log_handler):
        from phantom.ui.dashboard import SettingsScreen

        app = PhantomDashboard(
            stats=Stats(),
            config=default_config,
            log_handler=log_handler,
            on_toggle=MagicMock(return_value=True),
            on_quit=MagicMock(),
        )
        async with app.run_test() as pilot:
            await pilot.press("c")
            assert isinstance(app.screen, SettingsScreen)
