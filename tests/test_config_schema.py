"""Tests for phantom.config.schema."""

from __future__ import annotations

from phantom.config.schema import (
    AppSwitcherConfig,
    BrowserTabsConfig,
    CodeTypingConfig,
    HotkeyConfig,
    KeyboardConfig,
    MouseConfig,
    PhantomConfig,
    ScrollConfig,
    StealthConfig,
    TimingConfig,
)


class TestTimingConfig:
    def test_defaults(self):
        c = TimingConfig()
        assert c.interval_mean == 8.0
        assert c.interval_stddev == 4.0
        assert c.interval_min == 0.5
        assert c.idle_chance == 0.10
        assert c.idle_min == 15.0
        assert c.idle_max == 120.0

    def test_custom(self):
        c = TimingConfig(interval_mean=5.0, idle_chance=0.2)
        assert c.interval_mean == 5.0
        assert c.idle_chance == 0.2


class TestMouseConfig:
    def test_defaults(self):
        c = MouseConfig()
        assert c.enabled is True
        assert c.weight == 40.0
        assert c.min_distance == 50
        assert c.max_distance == 500
        assert c.bezier_steps == 100


class TestKeyboardConfig:
    def test_defaults(self):
        c = KeyboardConfig()
        assert c.enabled is True
        assert c.weight == 30.0
        assert c.max_presses == 3
        assert c.capslock_chance == 0.15

    def test_capslock_chance_clamped(self):
        c = KeyboardConfig(capslock_chance=2.0)
        assert c.capslock_chance == 1.0
        c = KeyboardConfig(capslock_chance=-0.5)
        assert c.capslock_chance == 0.0


class TestScrollConfig:
    def test_defaults(self):
        c = ScrollConfig()
        assert c.enabled is True
        assert c.weight == 15.0
        assert c.min_clicks == 1
        assert c.max_clicks == 5
        assert c.horizontal_chance == 0.1

    def test_horizontal_chance_clamped(self):
        c = ScrollConfig(horizontal_chance=1.5)
        assert c.horizontal_chance == 1.0
        c = ScrollConfig(horizontal_chance=-0.1)
        assert c.horizontal_chance == 0.0


class TestAppSwitcherConfig:
    def test_defaults(self):
        c = AppSwitcherConfig()
        assert c.enabled is False
        assert c.weight == 10.0
        assert c.min_tabs == 1
        assert c.max_tabs == 3

    def test_tabs_validation(self):
        c = AppSwitcherConfig(min_tabs=0, max_tabs=2)
        assert c.min_tabs == 1
        c = AppSwitcherConfig(min_tabs=5, max_tabs=3)
        assert c.max_tabs == 5


class TestBrowserTabsConfig:
    def test_defaults(self):
        c = BrowserTabsConfig()
        assert c.enabled is False
        assert c.weight == 5.0
        assert c.min_tabs == 1
        assert c.max_tabs == 4

    def test_tabs_validation(self):
        c = BrowserTabsConfig(min_tabs=0, max_tabs=2)
        assert c.min_tabs == 1
        c = BrowserTabsConfig(min_tabs=5, max_tabs=3)
        assert c.max_tabs == 5


class TestCodeTypingConfig:
    def test_defaults(self):
        c = CodeTypingConfig()
        assert c.enabled is False
        assert c.weight == 20.0
        assert c.min_chars == 10
        assert c.max_chars == 60
        assert c.char_delay_min == 0.05
        assert c.char_delay_max == 0.15

    def test_chars_validation(self):
        c = CodeTypingConfig(min_chars=0, max_chars=5)
        assert c.min_chars == 1
        c = CodeTypingConfig(min_chars=10, max_chars=5)
        assert c.max_chars == 10

    def test_delay_validation(self):
        c = CodeTypingConfig(char_delay_min=0.001, char_delay_max=0.005)
        assert c.char_delay_min == 0.01  # clamped to min 0.01
        assert c.char_delay_max == 0.01  # clamped to >= min


class TestHotkeyConfig:
    def test_defaults(self):
        c = HotkeyConfig()
        assert c.toggle == "<ctrl>+<alt>+s"
        assert c.quit == "<ctrl>+<alt>+q"
        assert c.hide_tray == "<ctrl>+<alt>+h"
        assert c.code_typing == "<ctrl>+<alt>+t"


class TestStealthConfig:
    def test_defaults(self):
        c = StealthConfig()
        assert c.rename_process is True
        assert c.process_name == "system_service"
        assert c.hide_tray is False


class TestPhantomConfig:
    def test_defaults(self):
        c = PhantomConfig()
        assert isinstance(c.timing, TimingConfig)
        assert isinstance(c.mouse, MouseConfig)
        assert isinstance(c.keyboard, KeyboardConfig)
        assert isinstance(c.scroll, ScrollConfig)
        assert isinstance(c.app_switcher, AppSwitcherConfig)
        assert isinstance(c.browser_tabs, BrowserTabsConfig)
        assert isinstance(c.hotkeys, HotkeyConfig)
        assert isinstance(c.stealth, StealthConfig)

    def test_simulator_weights_default(self):
        c = PhantomConfig()
        weights = c.simulator_weights()
        assert weights == {"mouse": 40.0, "keyboard": 30.0, "scroll": 15.0}

    def test_simulator_weights_all_enabled(self):
        c = PhantomConfig(
            app_switcher=AppSwitcherConfig(enabled=True),
            browser_tabs=BrowserTabsConfig(enabled=True),
        )
        weights = c.simulator_weights()
        assert len(weights) == 5
        assert "app_switcher" in weights
        assert "browser_tabs" in weights

    def test_simulator_weights_none_enabled(self):
        c = PhantomConfig(
            mouse=MouseConfig(enabled=False),
            keyboard=KeyboardConfig(enabled=False),
            scroll=ScrollConfig(enabled=False),
        )
        assert c.simulator_weights() == {}

    def test_simulator_weights_custom_weight(self):
        c = PhantomConfig(mouse=MouseConfig(weight=99.0))
        assert c.simulator_weights()["mouse"] == 99.0
