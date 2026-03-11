"""Tests for phantom.ui.tray."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from phantom.ui.tray import TrayIcon


class TestTrayIcon:
    def _make_tray(self):
        on_toggle = MagicMock(return_value=True)
        on_quit = MagicMock()
        on_hide = MagicMock()
        tray = TrayIcon(on_toggle=on_toggle, on_quit=on_quit, on_hide=on_hide)
        return tray, on_toggle, on_quit, on_hide

    def test_init(self):
        tray, _, _, _ = self._make_tray()
        assert tray._active is False
        assert tray._icon is None

    @patch("phantom.ui.tray.pystray.Icon")
    def test_run_creates_icon(self, MockIcon):
        tray, _, _, _ = self._make_tray()
        mock_icon = MockIcon.return_value
        tray.run()
        MockIcon.assert_called_once()
        mock_icon.run.assert_called_once()

    def test_stop_without_icon(self):
        tray, _, _, _ = self._make_tray()
        tray.stop()  # Should not raise

    def test_stop_with_icon(self):
        tray, _, _, _ = self._make_tray()
        tray._icon = MagicMock()
        tray.stop()
        tray._icon.stop.assert_called_once()

    def test_update_status_active(self):
        tray, _, _, _ = self._make_tray()
        tray._icon = MagicMock()
        tray.update_status(True)
        assert tray._active is True
        assert tray._icon.title == "Phantom - Active"
        tray._icon.update_menu.assert_called_once()

    def test_update_status_paused(self):
        tray, _, _, _ = self._make_tray()
        tray._icon = MagicMock()
        tray.update_status(False)
        assert tray._active is False
        assert tray._icon.title == "Phantom - Paused"

    def test_update_status_no_icon(self):
        tray, _, _, _ = self._make_tray()
        tray.update_status(True)  # No crash without icon
        assert tray._active is True

    def test_hide(self):
        tray, _, _, _ = self._make_tray()
        tray._icon = MagicMock()
        tray.hide()
        assert tray._icon.visible is False

    def test_hide_no_icon(self):
        tray, _, _, _ = self._make_tray()
        tray.hide()  # No crash

    def test_show(self):
        tray, _, _, _ = self._make_tray()
        tray._icon = MagicMock()
        tray.show()
        assert tray._icon.visible is True

    def test_show_no_icon(self):
        tray, _, _, _ = self._make_tray()
        tray.show()  # No crash

    def test_handle_toggle(self):
        tray, on_toggle, _, _ = self._make_tray()
        tray._icon = MagicMock()
        on_toggle.return_value = True
        tray._handle_toggle(MagicMock(), MagicMock())
        on_toggle.assert_called_once()
        assert tray._active is True

    def test_handle_quit(self):
        tray, _, on_quit, _ = self._make_tray()
        tray._handle_quit(MagicMock(), MagicMock())
        on_quit.assert_called_once()

    def test_handle_hide(self):
        tray, _, _, on_hide = self._make_tray()
        tray._handle_hide(MagicMock(), MagicMock())
        on_hide.assert_called_once()

    def test_build_menu(self):
        tray, _, _, _ = self._make_tray()
        menu = tray._build_menu()
        assert menu is not None
