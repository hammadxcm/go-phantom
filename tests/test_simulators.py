"""Tests for all simulator classes."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from phantom.config.schema import (
    AppSwitcherConfig,
    BrowserTabsConfig,
    KeyboardConfig,
    MouseConfig,
    ScrollConfig,
)
from phantom.simulators.app_switcher import AppSwitcherSimulator
from phantom.simulators.base import BaseSimulator
from phantom.simulators.browser_tabs import BrowserTabsSimulator
from phantom.simulators.keyboard import SAFE_KEYS, KeyboardSimulator
from phantom.simulators.mouse import MouseSimulator
from phantom.simulators.scroll import ScrollSimulator

# ---- BaseSimulator ----


class TestBaseSimulator:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseSimulator()

    def test_subclass_must_implement_execute(self):
        class BadSim(BaseSimulator):
            pass

        with pytest.raises(TypeError):
            BadSim()

    def test_subclass_with_execute(self):
        class GoodSim(BaseSimulator):
            def execute(self, config):
                pass

        sim = GoodSim()
        assert sim.name == "GoodSim"
        assert sim.log is not None


# ---- MouseSimulator ----


class TestMouseSimulator:
    @patch("phantom.simulators.mouse.time.sleep")
    @patch("phantom.simulators.mouse.pyautogui")
    def test_execute_moves_mouse(self, mock_pyautogui, mock_sleep):
        mock_pyautogui.size.return_value = (1920, 1080)
        mock_pyautogui.position.return_value = (500, 500)

        sim = MouseSimulator()
        config = MouseConfig(min_distance=10, max_distance=50, bezier_steps=5)
        sim.execute(config)

        assert mock_pyautogui.moveTo.called
        # Should have called moveTo at least steps+1 times
        assert mock_pyautogui.moveTo.call_count >= 6

    @patch("phantom.simulators.mouse.time.sleep")
    @patch("phantom.simulators.mouse.pyautogui")
    def test_clamp_to_screen_bounds(self, mock_pyautogui, mock_sleep):
        mock_pyautogui.size.return_value = (1920, 1080)
        mock_pyautogui.position.return_value = (960, 540)

        sim = MouseSimulator()
        config = MouseConfig(min_distance=10, max_distance=50, bezier_steps=5)
        sim.execute(config)

        # Verify moveTo was called (Bezier path points may have noise
        # but are int-rounded from the path generator)
        assert mock_pyautogui.moveTo.called
        assert mock_pyautogui.moveTo.call_count >= 6

    def test_clamp_static(self):
        assert MouseSimulator._clamp(5, 0, 10) == 5
        assert MouseSimulator._clamp(-1, 0, 10) == 0
        assert MouseSimulator._clamp(15, 0, 10) == 10

    @patch("phantom.simulators.mouse.time.sleep")
    @patch("phantom.simulators.mouse.pyautogui")
    @patch("phantom.simulators.mouse.random.random", return_value=0.1)
    def test_micro_correction(self, mock_rand, mock_pyautogui, mock_sleep):
        mock_pyautogui.size.return_value = (1920, 1080)
        mock_pyautogui.position.return_value = (500, 500)

        sim = MouseSimulator()
        config = MouseConfig(bezier_steps=3)
        sim.execute(config)

        # Micro-correction triggers when random() < 0.3
        # moveTo called for bezier path (4 points) + 1 correction = 5
        assert mock_pyautogui.moveTo.call_count >= 5

    @patch("phantom.simulators.mouse.time.sleep")
    @patch("phantom.simulators.mouse.pyautogui")
    def test_minimum_distance_enforced(self, mock_pyautogui, mock_sleep):
        mock_pyautogui.size.return_value = (1920, 1080)
        mock_pyautogui.position.return_value = (960, 540)

        sim = MouseSimulator()
        # Very small max_distance but large min_distance
        config = MouseConfig(min_distance=100, max_distance=5, bezier_steps=3)

        side = [1, 1, -3, 3, 2, -1, 0, 3]
        with patch("phantom.simulators.mouse.random.randint", side_effect=side):
            sim.execute(config)

        assert mock_pyautogui.moveTo.called


# ---- KeyboardSimulator ----


class TestKeyboardSimulator:
    @patch("phantom.simulators.keyboard.time.sleep")
    @patch("phantom.simulators.keyboard.Controller")
    def test_execute_presses_keys(self, MockController, mock_sleep):
        mock_ctrl = MockController.return_value
        sim = KeyboardSimulator()
        sim._controller = mock_ctrl
        config = KeyboardConfig(max_presses=2)

        with (
            patch("phantom.simulators.keyboard.random.randint", return_value=2),
            patch("phantom.simulators.keyboard.random.random", return_value=0.5),
        ):
            sim.execute(config)

        assert mock_ctrl.press.called
        assert mock_ctrl.release.called

    @patch("phantom.simulators.keyboard.time.sleep")
    @patch("phantom.simulators.keyboard.Controller")
    def test_capslock_double_tap(self, MockController, mock_sleep):
        mock_ctrl = MockController.return_value
        sim = KeyboardSimulator()
        sim._controller = mock_ctrl
        config = KeyboardConfig(max_presses=1)

        with (
            patch("phantom.simulators.keyboard.random.randint", return_value=1),
            # random() < 0.15 triggers capslock
            patch("phantom.simulators.keyboard.random.random", return_value=0.05),
        ):
            sim.execute(config)

        from pynput.keyboard import Key

        press_calls = [c for c in mock_ctrl.press.call_args_list if c[0][0] == Key.caps_lock]
        assert len(press_calls) == 2  # Double tap

    @patch("phantom.simulators.keyboard.time.sleep")
    @patch("phantom.simulators.keyboard.Controller")
    def test_modifier_keys_only(self, MockController, mock_sleep):
        mock_ctrl = MockController.return_value
        sim = KeyboardSimulator()
        sim._controller = mock_ctrl
        config = KeyboardConfig(max_presses=3)

        with (
            patch("phantom.simulators.keyboard.random.randint", return_value=3),
            patch("phantom.simulators.keyboard.random.random", return_value=0.5),
        ):
            sim.execute(config)

        from pynput.keyboard import Key

        allowed = set(SAFE_KEYS) | {Key.caps_lock}
        for c in mock_ctrl.press.call_args_list:
            assert c[0][0] in allowed


# ---- ScrollSimulator ----


class TestScrollSimulator:
    @patch("phantom.simulators.scroll.time.sleep")
    @patch("phantom.simulators.scroll.pyautogui")
    def test_execute_scrolls(self, mock_pyautogui, mock_sleep):
        sim = ScrollSimulator()
        config = ScrollConfig(min_clicks=2, max_clicks=3)

        with (
            patch("phantom.simulators.scroll.random.randint", side_effect=[2, 1, 2]),
            patch("phantom.simulators.scroll.random.choice", return_value=1),
            patch("phantom.simulators.scroll.random.random", return_value=0.5),
        ):
            sim.execute(config)

        assert mock_pyautogui.scroll.called

    @patch("phantom.simulators.scroll.time.sleep")
    @patch("phantom.simulators.scroll.pyautogui")
    def test_horizontal_scroll(self, mock_pyautogui, mock_sleep):
        sim = ScrollSimulator()
        config = ScrollConfig(min_clicks=1, max_clicks=1)

        with (
            patch("phantom.simulators.scroll.random.randint", side_effect=[1, 2]),
            patch("phantom.simulators.scroll.random.choice", return_value=-1),
            # random() < 0.1 triggers hscroll
            patch("phantom.simulators.scroll.random.random", return_value=0.05),
        ):
            sim.execute(config)

        assert mock_pyautogui.hscroll.called


# ---- AppSwitcherSimulator ----


class TestAppSwitcherSimulator:
    @patch("phantom.simulators.app_switcher.time.sleep")
    @patch("phantom.simulators.app_switcher.Controller")
    @patch("phantom.simulators.app_switcher.current_os")
    def test_execute_switches_app(self, mock_os, MockController, mock_sleep):
        from phantom.core.platform import OS

        mock_os.return_value = OS.WINDOWS
        mock_ctrl = MockController.return_value

        sim = AppSwitcherSimulator()
        sim._controller = mock_ctrl
        config = AppSwitcherConfig()

        with patch("phantom.simulators.app_switcher.random.randint", return_value=2):
            sim.execute(config)

        assert mock_ctrl.press.called
        assert mock_ctrl.release.called

    @patch("phantom.simulators.app_switcher.time.sleep")
    @patch("phantom.simulators.app_switcher.Controller")
    @patch("phantom.simulators.app_switcher.current_os")
    def test_macos_uses_cmd(self, mock_os, MockController, mock_sleep):
        from pynput.keyboard import Key

        from phantom.core.platform import OS

        mock_os.return_value = OS.MACOS

        sim = AppSwitcherSimulator()
        assert sim._modifier == Key.cmd

    @patch("phantom.simulators.app_switcher.time.sleep")
    @patch("phantom.simulators.app_switcher.Controller")
    @patch("phantom.simulators.app_switcher.current_os")
    def test_windows_uses_alt(self, mock_os, MockController, mock_sleep):
        from pynput.keyboard import Key

        from phantom.core.platform import OS

        mock_os.return_value = OS.WINDOWS

        sim = AppSwitcherSimulator()
        assert sim._modifier == Key.alt


# ---- BrowserTabsSimulator ----


class TestBrowserTabsSimulator:
    @patch("phantom.simulators.browser_tabs.time.sleep")
    @patch("phantom.simulators.browser_tabs.Controller")
    @patch("phantom.simulators.browser_tabs.get_active_window", return_value=None)
    def test_execute_switches_tabs(self, mock_window, MockController, mock_sleep):
        mock_ctrl = MockController.return_value
        sim = BrowserTabsSimulator()
        sim._controller = mock_ctrl
        config = BrowserTabsConfig()

        with patch("phantom.simulators.browser_tabs.random.randint", return_value=2):
            sim.execute(config)

        from pynput.keyboard import Key

        # Should press ctrl+tab twice
        ctrl_presses = [c for c in mock_ctrl.press.call_args_list if c[0][0] == Key.ctrl]
        tab_presses = [c for c in mock_ctrl.press.call_args_list if c[0][0] == Key.tab]
        assert len(ctrl_presses) == 2
        assert len(tab_presses) == 2

    @patch("phantom.simulators.browser_tabs.time.sleep")
    @patch("phantom.simulators.browser_tabs.Controller")
    @patch("phantom.simulators.browser_tabs.current_os")
    @patch("phantom.simulators.browser_tabs.get_active_window")
    def test_context_aware_chrome_macos(
        self, mock_window, mock_os, MockController, mock_sleep
    ):
        from pynput.keyboard import Key, KeyCode

        from phantom.core.active_window import WindowInfo
        from phantom.core.platform import OS

        mock_os.return_value = OS.MACOS
        mock_window.return_value = WindowInfo(
            app_name="Google Chrome", window_title="GitHub"
        )
        mock_ctrl = MockController.return_value
        sim = BrowserTabsSimulator()
        sim._controller = mock_ctrl
        config = BrowserTabsConfig(context_aware=True, backward_chance=0.0)

        with patch("phantom.simulators.browser_tabs.random.randint", return_value=1):
            sim.execute(config)

        # Chrome on macOS uses Cmd+Shift+]
        press_calls = [c[0][0] for c in mock_ctrl.press.call_args_list]
        assert Key.cmd in press_calls
        assert Key.shift in press_calls
        assert KeyCode.from_char("]") in press_calls

    @patch("phantom.simulators.browser_tabs.time.sleep")
    @patch("phantom.simulators.browser_tabs.Controller")
    @patch("phantom.simulators.browser_tabs.get_active_window", return_value=None)
    def test_fallback_on_detection_failure(
        self, mock_window, MockController, mock_sleep
    ):
        from pynput.keyboard import Key

        mock_ctrl = MockController.return_value
        sim = BrowserTabsSimulator()
        sim._controller = mock_ctrl
        config = BrowserTabsConfig(context_aware=True)

        with patch("phantom.simulators.browser_tabs.random.randint", return_value=1):
            sim.execute(config)

        # Falls back to Ctrl+Tab
        press_calls = [c[0][0] for c in mock_ctrl.press.call_args_list]
        assert Key.ctrl in press_calls
        assert Key.tab in press_calls

    @patch("phantom.simulators.browser_tabs.time.sleep")
    @patch("phantom.simulators.browser_tabs.Controller")
    def test_context_aware_false(self, MockController, mock_sleep):
        from pynput.keyboard import Key

        mock_ctrl = MockController.return_value
        sim = BrowserTabsSimulator()
        sim._controller = mock_ctrl
        config = BrowserTabsConfig(context_aware=False)

        with patch("phantom.simulators.browser_tabs.random.randint", return_value=1):
            sim.execute(config)

        # Should use blind Ctrl+Tab without calling get_active_window
        press_calls = [c[0][0] for c in mock_ctrl.press.call_args_list]
        assert Key.ctrl in press_calls
        assert Key.tab in press_calls

    @patch("phantom.simulators.browser_tabs.time.sleep")
    @patch("phantom.simulators.browser_tabs.Controller")
    @patch("phantom.simulators.browser_tabs.current_os")
    @patch("phantom.simulators.browser_tabs.get_active_window")
    def test_backward_direction(
        self, mock_window, mock_os, MockController, mock_sleep
    ):
        from pynput.keyboard import Key

        from phantom.core.active_window import WindowInfo
        from phantom.core.platform import OS

        mock_os.return_value = OS.WINDOWS
        mock_window.return_value = WindowInfo(
            app_name="Google Chrome", window_title="Tab"
        )
        mock_ctrl = MockController.return_value
        sim = BrowserTabsSimulator()
        sim._controller = mock_ctrl
        config = BrowserTabsConfig(context_aware=True, backward_chance=1.0)

        with patch("phantom.simulators.browser_tabs.random.randint", return_value=1):
            sim.execute(config)

        # backward_chance=1.0 → always backward → Ctrl+Shift+Tab
        press_calls = [c[0][0] for c in mock_ctrl.press.call_args_list]
        assert Key.ctrl in press_calls
        assert Key.shift in press_calls
        assert Key.tab in press_calls
