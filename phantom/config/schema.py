"""Dataclasses for configuration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TimingConfig:
    interval_mean: float = 8.0
    interval_stddev: float = 4.0
    interval_min: float = 0.5
    idle_chance: float = 0.10
    idle_min: float = 15.0
    idle_max: float = 120.0


@dataclass
class MouseConfig:
    enabled: bool = True
    weight: float = 40.0
    min_distance: int = 50
    max_distance: int = 500
    bezier_steps: int = 100


@dataclass
class KeyboardConfig:
    enabled: bool = True
    weight: float = 30.0
    max_presses: int = 3


@dataclass
class ScrollConfig:
    enabled: bool = True
    weight: float = 15.0
    min_clicks: int = 1
    max_clicks: int = 5


@dataclass
class AppSwitcherConfig:
    enabled: bool = False
    weight: float = 10.0


@dataclass
class BrowserTabsConfig:
    enabled: bool = False
    weight: float = 5.0


@dataclass
class HotkeyConfig:
    toggle: str = "<ctrl>+<alt>+s"
    quit: str = "<ctrl>+<alt>+q"
    hide_tray: str = "<ctrl>+<alt>+h"


@dataclass
class StealthConfig:
    rename_process: bool = True
    process_name: str = "system_service"
    hide_tray: bool = False


@dataclass
class PhantomConfig:
    timing: TimingConfig = field(default_factory=TimingConfig)
    mouse: MouseConfig = field(default_factory=MouseConfig)
    keyboard: KeyboardConfig = field(default_factory=KeyboardConfig)
    scroll: ScrollConfig = field(default_factory=ScrollConfig)
    app_switcher: AppSwitcherConfig = field(default_factory=AppSwitcherConfig)
    browser_tabs: BrowserTabsConfig = field(default_factory=BrowserTabsConfig)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    stealth: StealthConfig = field(default_factory=StealthConfig)

    def simulator_weights(self) -> dict[str, float]:
        """Return mapping of enabled simulator names to their weights."""
        sims: dict[str, float] = {}
        if self.mouse.enabled:
            sims["mouse"] = self.mouse.weight
        if self.keyboard.enabled:
            sims["keyboard"] = self.keyboard.weight
        if self.scroll.enabled:
            sims["scroll"] = self.scroll.weight
        if self.app_switcher.enabled:
            sims["app_switcher"] = self.app_switcher.weight
        if self.browser_tabs.enabled:
            sims["browser_tabs"] = self.browser_tabs.weight
        return sims
