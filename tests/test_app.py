"""Tests for phantom.app."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from phantom.config.schema import PhantomConfig, StealthConfig
from phantom.ui.modes import OutputMode


@patch("phantom.app.HotkeyManager")
@patch("phantom.app.TrayIcon")
@patch("phantom.app.Scheduler")
@patch("phantom.app.ConfigManager")
class TestPhantomApp:
    def test_init(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        PhantomApp()
        MockCM.assert_called_once()
        MockSched.assert_called_once()
        MockTray.assert_called_once()
        MockHotkey.assert_called_once()

    def test_init_with_config_path(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        PhantomApp(config_path="/tmp/test.json")
        MockCM.assert_called_once_with("/tmp/test.json")

    @patch("phantom.app.mask_process_name")
    @patch("phantom.app.check_platform_requirements")
    @patch("pyautogui.FAILSAFE", False)
    @patch("pyautogui.PAUSE", 0)
    def test_run(
        self,
        mock_check,
        mock_mask,
        MockCM,
        MockSched,
        MockTray,
        MockHotkey,
    ):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        app = PhantomApp()
        app.run()

        mock_check.assert_called_once()
        mock_mask.assert_called_once_with("system_service")
        app._hotkey_mgr.start.assert_called_once()
        app._scheduler.start.assert_called_once()
        app._tray.update_status.assert_called_with(True)
        app._tray.run.assert_called_once()

    @patch("phantom.app.mask_process_name")
    @patch("phantom.app.check_platform_requirements")
    @patch("pyautogui.FAILSAFE", False)
    @patch("pyautogui.PAUSE", 0)
    def test_run_no_rename(
        self,
        mock_check,
        mock_mask,
        MockCM,
        MockSched,
        MockTray,
        MockHotkey,
    ):
        config = PhantomConfig(stealth=StealthConfig(rename_process=False))
        MockCM.return_value.config = config
        from phantom.app import PhantomApp

        app = PhantomApp()
        app.run()
        mock_mask.assert_not_called()

    def test_handle_toggle(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        MockSched.return_value.toggle.return_value = True
        from phantom.app import PhantomApp

        app = PhantomApp()
        result = app._handle_toggle()
        assert result is True

    def test_handle_hotkey_toggle(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        MockSched.return_value.toggle.return_value = False
        from phantom.app import PhantomApp

        app = PhantomApp()
        app._handle_hotkey_toggle()
        app._tray.update_status.assert_called_with(False)

    def test_handle_quit(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        app = PhantomApp()
        app._handle_quit()
        app._scheduler.shutdown.assert_called_once()
        app._hotkey_mgr.stop.assert_called_once()
        app._tray.stop.assert_called_once()

    def test_handle_hide_hides(self, MockCM, MockSched, MockTray, MockHotkey):
        config = PhantomConfig(stealth=StealthConfig(hide_tray=False))
        MockCM.return_value.config = config
        from phantom.app import PhantomApp

        app = PhantomApp()
        app._handle_hide()
        app._tray.hide.assert_called_once()
        assert config.stealth.hide_tray is True

    def test_handle_hide_shows(self, MockCM, MockSched, MockTray, MockHotkey):
        config = PhantomConfig(stealth=StealthConfig(hide_tray=True))
        MockCM.return_value.config = config
        from phantom.app import PhantomApp

        app = PhantomApp()
        app._handle_hide()
        app._tray.show.assert_called_once()
        assert config.stealth.hide_tray is False

    @patch("phantom.app._print_logo")
    @patch("phantom.app._print_status")
    @patch("phantom.app.mask_process_name")
    @patch("phantom.app.check_platform_requirements")
    @patch("pyautogui.FAILSAFE", False)
    @patch("pyautogui.PAUSE", 0)
    def test_run_tui_mode(
        self,
        mock_check,
        mock_mask,
        mock_status,
        mock_logo,
        MockCM,
        MockSched,
        MockTray,
        MockHotkey,
    ):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        app = PhantomApp()
        mock_handler = MagicMock()
        with patch("phantom.ui.dashboard.Dashboard") as MockDash:
            app.run(mode=OutputMode.TUI, log_handler=mock_handler)
            MockDash.assert_called_once()
            MockDash.return_value.run.assert_called_once()

    @patch("phantom.app._print_logo")
    @patch("phantom.app._print_status")
    @patch("phantom.app.mask_process_name")
    @patch("phantom.app.check_platform_requirements")
    @patch("pyautogui.FAILSAFE", False)
    @patch("pyautogui.PAUSE", 0)
    def test_run_tail_mode(
        self,
        mock_check,
        mock_mask,
        mock_status,
        mock_logo,
        MockCM,
        MockSched,
        MockTray,
        MockHotkey,
    ):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        app = PhantomApp()
        # Pre-set the stop event so _run_tail_mode doesn't block
        app._tail_stop.set()
        app.run(mode=OutputMode.TAIL)
        mock_logo.assert_called_once()
        mock_status.assert_called_with("on")

    @patch("phantom.app._print_logo")
    @patch("phantom.app._print_status")
    @patch("phantom.app.mask_process_name")
    @patch("phantom.app.check_platform_requirements")
    @patch("pyautogui.FAILSAFE", False)
    @patch("pyautogui.PAUSE", 0)
    def test_run_ghost_mode(
        self,
        mock_check,
        mock_mask,
        mock_status,
        mock_logo,
        MockCM,
        MockSched,
        MockTray,
        MockHotkey,
    ):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        app = PhantomApp()
        app.run(mode=OutputMode.GHOST)
        app._tray.update_status.assert_called_with(True)
        app._tray.run.assert_called_once()

    def test_apply_overrides_only(self, MockCM, MockSched, MockTray, MockHotkey):
        config = PhantomConfig()
        MockCM.return_value.config = config
        from phantom.app import PhantomApp

        PhantomApp(cli_overrides={"_only": {"mouse"}})
        assert config.mouse.enabled is True
        assert config.keyboard.enabled is False
        assert config.scroll.enabled is False
        assert config.app_switcher.enabled is False
        assert config.browser_tabs.enabled is False

    def test_apply_overrides_enable_disable(self, MockCM, MockSched, MockTray, MockHotkey):
        config = PhantomConfig()
        MockCM.return_value.config = config
        from phantom.app import PhantomApp

        PhantomApp(cli_overrides={"_enable": {"app_switcher"}, "_disable": {"scroll"}})
        assert config.app_switcher.enabled is True
        assert config.scroll.enabled is False

    def test_apply_overrides_section(self, MockCM, MockSched, MockTray, MockHotkey):
        config = PhantomConfig()
        MockCM.return_value.config = config
        from phantom.app import PhantomApp

        PhantomApp(cli_overrides={"timing": {"interval_mean": 3.0}})
        MockCM.return_value.update.assert_called_with("timing", interval_mean=3.0)

    def test_handle_sim_toggle(self, MockCM, MockSched, MockTray, MockHotkey):
        config = PhantomConfig()
        MockCM.return_value.config = config
        from phantom.app import PhantomApp

        app = PhantomApp()
        # Should not raise; just logs
        app._handle_sim_toggle("mouse")

    def test_handle_sim_pause(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        MockSched.return_value.toggle_sim_pause.return_value = True
        from phantom.app import PhantomApp

        app = PhantomApp()
        result = app._handle_sim_pause("mouse")
        assert result is True
        app._scheduler.toggle_sim_pause.assert_called_with("mouse")

    def test_handle_save_config(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        app = PhantomApp()
        app._handle_save_config()
        app._config_mgr.save.assert_called_once()

    @patch("phantom.app.mask_process_name")
    @patch("phantom.app.check_platform_requirements")
    @patch("pyautogui.FAILSAFE", False)
    @patch("pyautogui.PAUSE", 0)
    def test_print_logo(
        self,
        mock_check,
        mock_mask,
        MockCM,
        MockSched,
        MockTray,
        MockHotkey,
    ):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import _print_logo

        with patch("rich.console.Console"):
            _print_logo(PhantomConfig())

    def test_print_status_on(self, MockCM, MockSched, MockTray, MockHotkey):
        from phantom.app import _print_status

        with patch("builtins.print"):
            _print_status("on")

    def test_print_status_off(self, MockCM, MockSched, MockTray, MockHotkey):
        from phantom.app import _print_status

        with patch("builtins.print"):
            _print_status("off")

    def test_print_status_quit(self, MockCM, MockSched, MockTray, MockHotkey):
        from phantom.app import _print_status

        with patch("builtins.print"):
            _print_status("quit")


def test_create_simulators():
    from phantom.app import PhantomApp

    sims = PhantomApp._create_simulators()
    expected = {
        "mouse",
        "keyboard",
        "scroll",
        "app_switcher",
        "browser_tabs",
        "code_typing",
    }
    assert set(sims.keys()) == expected
