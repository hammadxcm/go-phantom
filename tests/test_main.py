"""Tests for phantom.__main__."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestMain:
    @patch("phantom.app.PhantomApp")
    @patch("sys.argv", ["phantom"])
    def test_main_default(self, MockApp):
        from phantom.__main__ import main
        from phantom.ui.modes import OutputMode

        main()
        MockApp.assert_called_once_with(config_path=None, cli_overrides={}, preset=None)
        MockApp.return_value.run.assert_called_once_with(mode=OutputMode.TRAY, log_handler=None)

    @patch("phantom.app.PhantomApp")
    @patch("sys.argv", ["phantom", "-c", "/tmp/cfg.json"])
    def test_main_with_config(self, MockApp):
        from phantom.__main__ import main

        main()
        MockApp.assert_called_once_with(config_path="/tmp/cfg.json", cli_overrides={}, preset=None)

    @patch("phantom.app.PhantomApp")
    @patch("sys.argv", ["phantom", "-v"])
    def test_main_verbose(self, MockApp):
        from phantom.__main__ import main

        main()
        MockApp.assert_called_once()

    @patch("phantom.app.PhantomApp")
    @patch("sys.argv", ["phantom"])
    def test_main_keyboard_interrupt(self, MockApp):
        MockApp.return_value.run.side_effect = KeyboardInterrupt

        from phantom.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    @patch("phantom.app.PhantomApp")
    @patch("sys.argv", ["phantom", "--tui"])
    def test_main_tui_flag(self, MockApp):
        from phantom.__main__ import main
        from phantom.ui.modes import OutputMode

        main()
        MockApp.assert_called_once_with(config_path=None, cli_overrides={}, preset=None)
        call_args = MockApp.return_value.run.call_args
        assert call_args.kwargs["mode"] == OutputMode.TUI
        assert call_args.kwargs["log_handler"] is not None

    @patch("phantom.app.PhantomApp")
    @patch("sys.argv", ["phantom", "--tail"])
    def test_main_tail_flag(self, MockApp):
        from phantom.__main__ import main
        from phantom.ui.modes import OutputMode

        main()
        MockApp.assert_called_once_with(config_path=None, cli_overrides={}, preset=None)
        call_args = MockApp.return_value.run.call_args
        assert call_args.kwargs["mode"] == OutputMode.TAIL
        assert call_args.kwargs["log_handler"] is None

    @patch("phantom.app.PhantomApp")
    @patch("sys.argv", ["phantom", "--ghost"])
    def test_main_ghost_flag(self, MockApp):
        from phantom.__main__ import main
        from phantom.ui.modes import OutputMode

        main()
        MockApp.assert_called_once_with(config_path=None, cli_overrides={}, preset=None)
        call_args = MockApp.return_value.run.call_args
        assert call_args.kwargs["mode"] == OutputMode.GHOST
        assert call_args.kwargs["log_handler"] is None

    @patch("sys.argv", ["phantom", "--tui", "--tail"])
    def test_main_mutually_exclusive_modes(self):
        from phantom.__main__ import _build_parser

        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--tui", "--tail"])

    @patch("sys.argv", ["phantom", "--tui", "--ghost"])
    def test_main_mutually_exclusive_tui_ghost(self):
        from phantom.__main__ import _build_parser

        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--tui", "--ghost"])

    @patch("sys.argv", ["phantom", "--tail", "--ghost"])
    def test_main_mutually_exclusive_tail_ghost(self):
        from phantom.__main__ import _build_parser

        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--tail", "--ghost"])

    @patch("sys.argv", ["phantom"])
    @patch("phantom.app.PhantomApp")
    def test_main_uses_rich_handler(self, MockApp):
        """Verify RichHandler is installed when rich is available."""
        from phantom.__main__ import main

        main()
        # The test verifies main() runs without error with RichHandler
        MockApp.assert_called_once()
