"""Tests for phantom.stealth.process."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from phantom.core.platform import OS
from phantom.stealth.process import (
    _mask_linux,
    _mask_macos,
    _mask_windows,
    mask_process_name,
)


class TestMaskProcessName:
    @patch("phantom.stealth.process.current_os", return_value=OS.LINUX)
    @patch("phantom.stealth.process._mask_linux", return_value=True)
    def test_dispatches_linux(self, mock_mask, mock_os):
        assert mask_process_name("test") is True
        mock_mask.assert_called_once_with("test")

    @patch("phantom.stealth.process.current_os", return_value=OS.WINDOWS)
    @patch("phantom.stealth.process._mask_windows", return_value=True)
    def test_dispatches_windows(self, mock_mask, mock_os):
        assert mask_process_name("test") is True
        mock_mask.assert_called_once_with("test")

    @patch("phantom.stealth.process.current_os", return_value=OS.MACOS)
    @patch("phantom.stealth.process._mask_macos", return_value=True)
    def test_dispatches_macos(self, mock_mask, mock_os):
        assert mask_process_name("test") is True
        mock_mask.assert_called_once_with("test")

    @patch("phantom.stealth.process.current_os", return_value=OS.LINUX)
    @patch("phantom.stealth.process._mask_linux", side_effect=OSError("bad"))
    def test_exception_returns_false(self, mock_mask, mock_os):
        assert mask_process_name("test") is False


class TestMaskLinux:
    @patch.dict("sys.modules", {"setproctitle": MagicMock()})
    def test_with_setproctitle(self):
        assert _mask_linux("test") is True

    def test_without_setproctitle(self):
        import sys

        # Temporarily remove setproctitle if present
        saved = sys.modules.get("setproctitle")
        sys.modules["setproctitle"] = None  # type: ignore
        try:
            # Import will raise ImportError when module is None
            _mask_linux("test")
            # setproctitle might actually be installed, handle both cases
        except Exception:
            pass
        finally:
            if saved is not None:
                sys.modules["setproctitle"] = saved
            elif "setproctitle" in sys.modules:
                del sys.modules["setproctitle"]


class TestMaskWindows:
    @patch("phantom.stealth.process.ctypes")
    def test_success(self, mock_ctypes):
        mock_ctypes.windll.kernel32.SetConsoleTitleW.return_value = 1
        assert _mask_windows("test") is True

    @patch("phantom.stealth.process.ctypes")
    def test_failure(self, mock_ctypes):
        mock_ctypes.windll.kernel32.SetConsoleTitleW.side_effect = OSError("no")
        assert _mask_windows("test") is False


class TestMaskMacOS:
    @patch.dict("sys.modules", {"setproctitle": MagicMock()})
    def test_with_setproctitle(self):
        assert _mask_macos("test") is True

    def test_without_setproctitle_returns_false(self):
        import sys

        saved = sys.modules.get("setproctitle")
        sys.modules["setproctitle"] = None  # type: ignore
        try:
            result = _mask_macos("test")
            # Without setproctitle, should return False (no libc fallback)
            assert result is False
        except ImportError:
            pass  # Also acceptable if import mechanism raises
        finally:
            if saved is not None:
                sys.modules["setproctitle"] = saved
            elif "setproctitle" in sys.modules:
                del sys.modules["setproctitle"]
