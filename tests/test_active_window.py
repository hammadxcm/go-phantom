"""Tests for active window detection."""

from __future__ import annotations

import subprocess
import time
from unittest.mock import MagicMock, patch

import pytest

from phantom.core import active_window
from phantom.core.active_window import WindowInfo, get_active_window
from phantom.core.platform import OS


@pytest.fixture(autouse=True)
def _clear_cache():
    """Reset the module-level cache before each test."""
    active_window._cache = (0.0, None)


class TestMacOS:
    @patch("phantom.core.active_window.current_os", return_value=OS.MACOS)
    @patch("phantom.core.active_window.subprocess.run")
    def test_detects_app(self, mock_run, mock_os):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Google Chrome||GitHub - Mozilla Firefox\n",
        )
        result = get_active_window()
        assert result == WindowInfo(
            app_name="Google Chrome", window_title="GitHub - Mozilla Firefox"
        )

    @patch("phantom.core.active_window.current_os", return_value=OS.MACOS)
    @patch("phantom.core.active_window.subprocess.run")
    def test_returns_none_on_failure(self, mock_run, mock_os):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert get_active_window() is None


class TestWindows:
    @patch("phantom.core.active_window.current_os", return_value=OS.WINDOWS)
    def test_detects_app(self, mock_os):
        with patch("phantom.core.active_window._detect_windows") as mock_detect:
            mock_detect.return_value = WindowInfo(
                app_name="chrome.exe", window_title="New Tab - Google Chrome"
            )
            result = get_active_window()
            assert result is not None
            assert result.app_name == "chrome.exe"


class TestLinuxX11:
    @patch("phantom.core.active_window.is_wayland", return_value=False)
    @patch("phantom.core.active_window.current_os", return_value=OS.LINUX)
    @patch("phantom.core.active_window.subprocess.run")
    def test_detects_app(self, mock_run, mock_os, mock_wayland):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="12345678\n"),  # xdotool getactivewindow
            MagicMock(returncode=0, stdout="README.md\n"),  # getwindowname
            MagicMock(
                returncode=0,
                stdout='WM_CLASS(STRING) = "firefox", "Firefox"\n',
            ),
        ]
        result = get_active_window()
        assert result is not None
        assert result.app_name == "Firefox"
        assert result.window_title == "README.md"


class TestWayland:
    @patch("phantom.core.active_window.is_wayland", return_value=True)
    @patch("phantom.core.active_window.current_os", return_value=OS.LINUX)
    def test_returns_none(self, mock_os, mock_wayland):
        assert get_active_window() is None


class TestErrors:
    @patch("phantom.core.active_window.current_os", return_value=OS.MACOS)
    @patch(
        "phantom.core.active_window.subprocess.run",
        side_effect=FileNotFoundError("osascript not found"),
    )
    def test_file_not_found(self, mock_run, mock_os):
        assert get_active_window() is None

    @patch("phantom.core.active_window.current_os", return_value=OS.MACOS)
    @patch(
        "phantom.core.active_window.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="osascript", timeout=2),
    )
    def test_timeout(self, mock_run, mock_os):
        assert get_active_window() is None


class TestCache:
    @patch("phantom.core.active_window.current_os", return_value=OS.MACOS)
    @patch("phantom.core.active_window.subprocess.run")
    def test_cache_avoids_repeated_calls(self, mock_run, mock_os):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Safari||Apple\n",
        )
        result1 = get_active_window()
        result2 = get_active_window()
        assert result1 == result2
        assert mock_run.call_count == 1

    @patch("phantom.core.active_window.current_os", return_value=OS.MACOS)
    @patch("phantom.core.active_window.subprocess.run")
    def test_cache_expires(self, mock_run, mock_os):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Safari||Apple\n",
        )
        get_active_window()
        # Expire the cache
        active_window._cache = (time.monotonic() - 1.0, active_window._cache[1])
        get_active_window()
        assert mock_run.call_count == 2
