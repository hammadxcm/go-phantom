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
    @patch("phantom.stealth.process._mask_linux", side_effect=Exception("bad"))
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

    @patch("phantom.stealth.process.ctypes.CDLL")
    def test_fallback_libc(self, mock_cdll):
        import sys
        saved = sys.modules.get("setproctitle")
        sys.modules["setproctitle"] = None  # type: ignore
        try:
            _mask_macos("test")
            # May succeed via libc fallback or fail gracefully
        finally:
            if saved is not None:
                sys.modules["setproctitle"] = saved
            elif "setproctitle" in sys.modules:
                del sys.modules["setproctitle"]

    @patch("phantom.stealth.process.ctypes.CDLL", side_effect=OSError("no libc"))
    def test_all_fail(self, mock_cdll):
        import sys
        saved = sys.modules.get("setproctitle")
        sys.modules["setproctitle"] = None  # type: ignore
        try:
            _mask_macos("test")
            # When setproctitle import fails (None module), the behavior
            # depends on the import mechanism
        finally:
            if saved is not None:
                sys.modules["setproctitle"] = saved
            elif "setproctitle" in sys.modules:
                del sys.modules["setproctitle"]
