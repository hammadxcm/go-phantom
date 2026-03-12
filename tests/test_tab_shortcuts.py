"""Tests for tab shortcut registry."""

from __future__ import annotations

from pynput.keyboard import Key, KeyCode

from phantom.core.platform import OS
from phantom.core.tab_shortcuts import lookup_shortcut


class TestLookupShortcut:
    def test_chrome_macos(self):
        s = lookup_shortcut("Google Chrome", OS.MACOS)
        assert s.forward == (Key.cmd, Key.shift, KeyCode.from_char("]"))
        assert s.backward == (Key.cmd, Key.shift, KeyCode.from_char("["))

    def test_chrome_windows(self):
        s = lookup_shortcut("Google Chrome", OS.WINDOWS)
        assert s.forward == (Key.ctrl, Key.tab)
        assert s.backward == (Key.ctrl, Key.shift, Key.tab)

    def test_firefox_linux(self):
        s = lookup_shortcut("Firefox", OS.LINUX)
        assert s.forward == (Key.ctrl, Key.tab)

    def test_vscode_macos_uses_ctrl(self):
        s = lookup_shortcut("Code", OS.MACOS)
        assert s.forward == (Key.ctrl, Key.tab)

    def test_vscode_windows(self):
        s = lookup_shortcut("Code", OS.WINDOWS)
        assert s.forward == (Key.ctrl, Key.tab)

    def test_cursor_ide(self):
        s = lookup_shortcut("Cursor", OS.MACOS)
        assert s.forward == (Key.ctrl, Key.tab)

    def test_iterm_macos(self):
        s = lookup_shortcut("iTerm2", OS.MACOS)
        assert s.forward == (Key.cmd, Key.shift, KeyCode.from_char("]"))

    def test_kitty_linux(self):
        s = lookup_shortcut("kitty", OS.LINUX)
        assert s.forward == (Key.ctrl, Key.shift, Key.right)
        assert s.backward == (Key.ctrl, Key.shift, Key.left)

    def test_gnome_terminal(self):
        s = lookup_shortcut("gnome-terminal", OS.LINUX)
        assert s.forward == (Key.ctrl, Key.page_down)
        assert s.backward == (Key.ctrl, Key.page_up)

    def test_unknown_app_returns_default(self):
        s = lookup_shortcut("SomeRandomApp", OS.WINDOWS)
        assert s.forward == (Key.ctrl, Key.tab)
        assert s.backward == (Key.ctrl, Key.shift, Key.tab)

    def test_case_insensitive(self):
        s1 = lookup_shortcut("Google Chrome", OS.MACOS)
        s2 = lookup_shortcut("google-chrome", OS.MACOS)
        assert s1 == s2

    def test_windows_terminal_before_generic_terminal(self):
        s = lookup_shortcut("Windows Terminal", OS.WINDOWS)
        assert s.forward == (Key.ctrl, Key.tab)

    def test_macos_terminal(self):
        s = lookup_shortcut("Terminal", OS.MACOS)
        assert s.forward == (Key.cmd, Key.shift, KeyCode.from_char("]"))
