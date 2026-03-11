"""Tests for phantom.app."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from phantom.config.schema import PhantomConfig, StealthConfig


class TestPhantomApp:
    @patch("phantom.app.HotkeyManager")
    @patch("phantom.app.TrayIcon")
    @patch("phantom.app.Scheduler")
    @patch("phantom.app.ConfigManager")
    def test_init(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        app = PhantomApp()
        MockCM.assert_called_once()
        MockSched.assert_called_once()
        MockTray.assert_called_once()
        MockHotkey.assert_called_once()

    @patch("phantom.app.HotkeyManager")
    @patch("phantom.app.TrayIcon")
    @patch("phantom.app.Scheduler")
    @patch("phantom.app.ConfigManager")
    def test_init_with_config_path(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        app = PhantomApp(config_path="/tmp/test.json")
        MockCM.assert_called_once_with("/tmp/test.json")

    @patch("phantom.app.mask_process_name")
    @patch("phantom.app.check_platform_requirements")
    @patch("phantom.app.pyautogui")
    @patch("phantom.app.HotkeyManager")
    @patch("phantom.app.TrayIcon")
    @patch("phantom.app.Scheduler")
    @patch("phantom.app.ConfigManager")
    def test_run(self, MockCM, MockSched, MockTray, MockHotkey, mock_pyautogui, mock_check, mock_mask):
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
    @patch("phantom.app.pyautogui")
    @patch("phantom.app.HotkeyManager")
    @patch("phantom.app.TrayIcon")
    @patch("phantom.app.Scheduler")
    @patch("phantom.app.ConfigManager")
    def test_run_no_rename(self, MockCM, MockSched, MockTray, MockHotkey, mock_pyautogui, mock_check, mock_mask):
        config = PhantomConfig(stealth=StealthConfig(rename_process=False))
        MockCM.return_value.config = config
        from phantom.app import PhantomApp

        app = PhantomApp()
        app.run()
        mock_mask.assert_not_called()

    @patch("phantom.app.HotkeyManager")
    @patch("phantom.app.TrayIcon")
    @patch("phantom.app.Scheduler")
    @patch("phantom.app.ConfigManager")
    def test_handle_toggle(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        MockSched.return_value.toggle.return_value = True
        from phantom.app import PhantomApp

        app = PhantomApp()
        result = app._handle_toggle()
        assert result is True

    @patch("phantom.app.HotkeyManager")
    @patch("phantom.app.TrayIcon")
    @patch("phantom.app.Scheduler")
    @patch("phantom.app.ConfigManager")
    def test_handle_hotkey_toggle(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        MockSched.return_value.toggle.return_value = False
        from phantom.app import PhantomApp

        app = PhantomApp()
        app._handle_hotkey_toggle()
        app._tray.update_status.assert_called_with(False)

    @patch("phantom.app.HotkeyManager")
    @patch("phantom.app.TrayIcon")
    @patch("phantom.app.Scheduler")
    @patch("phantom.app.ConfigManager")
    def test_handle_quit(self, MockCM, MockSched, MockTray, MockHotkey):
        MockCM.return_value.config = PhantomConfig()
        from phantom.app import PhantomApp

        app = PhantomApp()
        app._handle_quit()
        app._scheduler.shutdown.assert_called_once()
        app._hotkey_mgr.stop.assert_called_once()
        app._tray.stop.assert_called_once()

    @patch("phantom.app.HotkeyManager")
    @patch("phantom.app.TrayIcon")
    @patch("phantom.app.Scheduler")
    @patch("phantom.app.ConfigManager")
    def test_handle_hide_hides(self, MockCM, MockSched, MockTray, MockHotkey):
        config = PhantomConfig(stealth=StealthConfig(hide_tray=False))
        MockCM.return_value.config = config
        from phantom.app import PhantomApp

        app = PhantomApp()
        app._handle_hide()
        app._tray.hide.assert_called_once()
        assert config.stealth.hide_tray is True

    @patch("phantom.app.HotkeyManager")
    @patch("phantom.app.TrayIcon")
    @patch("phantom.app.Scheduler")
    @patch("phantom.app.ConfigManager")
    def test_handle_hide_shows(self, MockCM, MockSched, MockTray, MockHotkey):
        config = PhantomConfig(stealth=StealthConfig(hide_tray=True))
        MockCM.return_value.config = config
        from phantom.app import PhantomApp

        app = PhantomApp()
        app._handle_hide()
        app._tray.show.assert_called_once()
        assert config.stealth.hide_tray is False

    def test_create_simulators(self):
        from phantom.app import PhantomApp

        sims = PhantomApp._create_simulators()
        assert set(sims.keys()) == {"mouse", "keyboard", "scroll", "app_switcher", "browser_tabs"}
