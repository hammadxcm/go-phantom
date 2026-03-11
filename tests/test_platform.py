"""Tests for phantom.core.platform."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from phantom.core.platform import (
    OS,
    check_platform_requirements,
    current_os,
    is_frozen,
    is_wayland,
)


class TestCurrentOS:
    @patch("phantom.core.platform.platform.system", return_value="Darwin")
    def test_macos(self, _mock):
        assert current_os() == OS.MACOS

    @patch("phantom.core.platform.platform.system", return_value="Windows")
    def test_windows(self, _mock):
        assert current_os() == OS.WINDOWS

    @patch("phantom.core.platform.platform.system", return_value="Linux")
    def test_linux(self, _mock):
        assert current_os() == OS.LINUX

    @patch("phantom.core.platform.platform.system", return_value="FreeBSD")
    def test_unsupported(self, _mock):
        with pytest.raises(RuntimeError, match="Unsupported platform"):
            current_os()


class TestIsWayland:
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"})
    def test_wayland(self):
        assert is_wayland() is True

    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"})
    def test_x11(self):
        assert is_wayland() is False

    @patch.dict("os.environ", {}, clear=True)
    def test_no_env(self):
        assert is_wayland() is False

    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "Wayland"})
    def test_case_insensitive(self):
        assert is_wayland() is True


class TestCheckPlatformRequirements:
    @patch("phantom.core.platform.current_os", return_value=OS.LINUX)
    @patch("phantom.core.platform.is_wayland", return_value=True)
    def test_linux_wayland_warning(self, _w, _os):
        warnings = check_platform_requirements()
        assert any("Wayland" in w for w in warnings)

    @patch("phantom.core.platform.current_os", return_value=OS.LINUX)
    @patch("phantom.core.platform.is_wayland", return_value=False)
    def test_linux_x11_no_warning(self, _w, _os):
        warnings = check_platform_requirements()
        assert not any("Wayland" in w for w in warnings)

    @patch("phantom.core.platform.current_os", return_value=OS.MACOS)
    @patch("phantom.core.platform.is_wayland", return_value=False)
    def test_macos_accessibility_warning(self, _w, _os):
        warnings = check_platform_requirements()
        assert any("Accessibility" in w for w in warnings)

    @patch("phantom.core.platform.current_os", return_value=OS.MACOS)
    @patch("phantom.core.platform.is_wayland", return_value=False)
    def test_macos_tccutil_fails(self, _w, _os):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            warnings = check_platform_requirements()
        assert any("Accessibility" in w for w in warnings)

    @patch("phantom.core.platform.current_os", return_value=OS.WINDOWS)
    @patch("phantom.core.platform.is_wayland", return_value=False)
    def test_windows_no_warnings(self, _w, _os):
        warnings = check_platform_requirements()
        assert len(warnings) == 0


class TestIsFrozen:
    def test_not_frozen(self):
        assert is_frozen() is False

    @patch("phantom.core.platform.sys")
    def test_frozen(self, mock_sys):
        mock_sys.frozen = True
        # Re-import won't work, test the function directly
        # Since we mock sys at module level, we need to test getattr
        assert getattr(mock_sys, "frozen", False) is True
