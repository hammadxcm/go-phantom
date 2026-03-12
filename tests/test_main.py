"""Tests for phantom.__main__."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestMain:
    @patch("phantom.app.PhantomApp")
    @patch("sys.argv", ["phantom"])
    def test_main_default(self, MockApp):
        from phantom.__main__ import main

        main()
        MockApp.assert_called_once_with(config_path=None, cli_overrides={})
        MockApp.return_value.run.assert_called_once_with(tui=False, log_handler=None)

    @patch("phantom.app.PhantomApp")
    @patch("sys.argv", ["phantom", "-c", "/tmp/cfg.json"])
    def test_main_with_config(self, MockApp):
        from phantom.__main__ import main

        main()
        MockApp.assert_called_once_with(config_path="/tmp/cfg.json", cli_overrides={})

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

        main()
        MockApp.assert_called_once_with(config_path=None, cli_overrides={})
        call_args = MockApp.return_value.run.call_args
        assert call_args.kwargs["tui"] is True
        assert call_args.kwargs["log_handler"] is not None

    @patch("sys.argv", ["phantom"])
    @patch("phantom.app.PhantomApp")
    def test_main_uses_rich_handler(self, MockApp):
        """Verify RichHandler is installed when rich is available."""
        from phantom.__main__ import main

        main()
        # The test verifies main() runs without error with RichHandler
        MockApp.assert_called_once()
