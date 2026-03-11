"""Tests for phantom.hotkeys.manager."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from phantom.config.schema import HotkeyConfig
from phantom.hotkeys.manager import HotkeyManager


class TestHotkeyManager:
    @patch("phantom.hotkeys.manager.GlobalHotKeys")
    def test_init_registers_hotkeys(self, MockGlobalHotKeys):
        config = HotkeyConfig()
        on_toggle = MagicMock()
        on_quit = MagicMock()
        on_hide = MagicMock()

        HotkeyManager(config, on_toggle, on_quit, on_hide)

        MockGlobalHotKeys.assert_called_once()
        call_args = MockGlobalHotKeys.call_args[0][0]
        assert config.toggle in call_args
        assert config.quit in call_args
        assert config.hide_tray in call_args

    @patch("phantom.hotkeys.manager.GlobalHotKeys")
    def test_start(self, MockGlobalHotKeys):
        mock_listener = MockGlobalHotKeys.return_value
        config = HotkeyConfig()
        mgr = HotkeyManager(config, MagicMock(), MagicMock(), MagicMock())
        mgr.start()
        mock_listener.start.assert_called_once()

    @patch("phantom.hotkeys.manager.GlobalHotKeys")
    def test_stop(self, MockGlobalHotKeys):
        mock_listener = MockGlobalHotKeys.return_value
        config = HotkeyConfig()
        mgr = HotkeyManager(config, MagicMock(), MagicMock(), MagicMock())
        mgr.stop()
        mock_listener.stop.assert_called_once()

    @patch("phantom.hotkeys.manager.GlobalHotKeys")
    def test_custom_hotkeys(self, MockGlobalHotKeys):
        config = HotkeyConfig(
            toggle="<ctrl>+<shift>+t",
            quit="<ctrl>+<shift>+q",
            hide_tray="<ctrl>+<shift>+h",
        )
        HotkeyManager(config, MagicMock(), MagicMock(), MagicMock())
        call_args = MockGlobalHotKeys.call_args[0][0]
        assert "<ctrl>+<shift>+t" in call_args
        assert "<ctrl>+<shift>+q" in call_args
        assert "<ctrl>+<shift>+h" in call_args

    @patch("phantom.hotkeys.manager.GlobalHotKeys")
    def test_daemon_flag(self, MockGlobalHotKeys):
        mock_listener = MockGlobalHotKeys.return_value
        config = HotkeyConfig()
        HotkeyManager(config, MagicMock(), MagicMock(), MagicMock())
        assert mock_listener.daemon is True

    @patch("phantom.hotkeys.manager.GlobalHotKeys")
    def test_start_no_listener(self, MockGlobalHotKeys):
        config = HotkeyConfig()
        mgr = HotkeyManager(config, MagicMock(), MagicMock(), MagicMock())
        mgr._listener = None
        mgr.start()  # Should not raise

    @patch("phantom.hotkeys.manager.GlobalHotKeys")
    def test_stop_no_listener(self, MockGlobalHotKeys):
        config = HotkeyConfig()
        mgr = HotkeyManager(config, MagicMock(), MagicMock(), MagicMock())
        mgr._listener = None
        mgr.stop()  # Should not raise
