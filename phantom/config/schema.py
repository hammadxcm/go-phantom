"""Dataclasses for configuration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TimingConfig:
    """Timing parameters that govern action intervals and idle pauses.

    Attributes:
        interval_mean: Mean delay in seconds between simulated actions.
        interval_stddev: Standard deviation for the interval distribution.
        interval_min: Hard lower bound on the interval in seconds.
        idle_chance: Probability (0-1) of entering an idle pause each cycle.
        idle_min: Minimum idle pause duration in seconds.
        idle_max: Maximum idle pause duration in seconds.
    """

    interval_mean: float = 8.0
    interval_stddev: float = 4.0
    interval_min: float = 0.5
    idle_chance: float = 0.10
    idle_min: float = 15.0
    idle_max: float = 120.0

    def __post_init__(self) -> None:
        self.idle_chance = max(0.0, min(1.0, self.idle_chance))
        self.interval_min = max(0.01, self.interval_min)
        self.interval_mean = max(self.interval_min, self.interval_mean)
        self.interval_stddev = max(0.0, self.interval_stddev)
        self.idle_min = max(0.0, self.idle_min)
        self.idle_max = max(self.idle_min, self.idle_max)


@dataclass
class MouseConfig:
    """Configuration for the mouse-movement simulator.

    Attributes:
        enabled: Whether the mouse simulator is active.
        weight: Relative selection weight among enabled simulators.
        min_distance: Minimum cursor travel distance in pixels.
        max_distance: Maximum cursor travel distance in pixels.
        bezier_steps: Number of intermediate points on the Bezier curve.
    """

    enabled: bool = True
    weight: float = 40.0
    min_distance: int = 50
    max_distance: int = 500
    bezier_steps: int = 100

    def __post_init__(self) -> None:
        self.weight = max(0.0, self.weight)
        self.min_distance = max(0, self.min_distance)
        self.max_distance = max(self.min_distance, self.max_distance)
        self.bezier_steps = max(1, self.bezier_steps)


@dataclass
class KeyboardConfig:
    """Configuration for the keyboard simulator.

    Attributes:
        enabled: Whether the keyboard simulator is active.
        weight: Relative selection weight among enabled simulators.
        max_presses: Maximum number of key presses per action.
        capslock_chance: Probability (0-1) of a CapsLock double-tap instead of a modifier press.
    """

    enabled: bool = True
    weight: float = 30.0
    max_presses: int = 3
    capslock_chance: float = 0.15

    def __post_init__(self) -> None:
        self.weight = max(0.0, self.weight)
        self.max_presses = max(1, self.max_presses)
        self.capslock_chance = max(0.0, min(1.0, self.capslock_chance))


@dataclass
class ScrollConfig:
    """Configuration for the scroll-wheel simulator.

    Attributes:
        enabled: Whether the scroll simulator is active.
        weight: Relative selection weight among enabled simulators.
        min_clicks: Minimum number of scroll clicks per action.
        max_clicks: Maximum number of scroll clicks per action.
        horizontal_chance: Probability (0-1) of horizontal instead of vertical scroll.
    """

    enabled: bool = True
    weight: float = 15.0
    min_clicks: int = 1
    max_clicks: int = 5
    horizontal_chance: float = 0.1

    def __post_init__(self) -> None:
        self.weight = max(0.0, self.weight)
        self.min_clicks = max(1, self.min_clicks)
        self.max_clicks = max(self.min_clicks, self.max_clicks)
        self.horizontal_chance = max(0.0, min(1.0, self.horizontal_chance))


@dataclass
class AppSwitcherConfig:
    """Configuration for the application-switcher simulator.

    Attributes:
        enabled: Whether the app-switcher simulator is active.
        weight: Relative selection weight among enabled simulators.
        min_tabs: Minimum number of app switches per action.
        max_tabs: Maximum number of app switches per action.
    """

    enabled: bool = False
    weight: float = 10.0
    min_tabs: int = 1
    max_tabs: int = 3

    def __post_init__(self) -> None:
        self.weight = max(0.0, self.weight)
        self.min_tabs = max(1, self.min_tabs)
        self.max_tabs = max(self.min_tabs, self.max_tabs)


@dataclass
class BrowserTabsConfig:
    """Configuration for the browser-tab switching simulator.

    Attributes:
        enabled: Whether the browser-tabs simulator is active.
        weight: Relative selection weight among enabled simulators.
        context_aware: Use the active-window context to pick shortcuts.
        backward_chance: Probability (0-1) of navigating backward instead of forward.
        min_tabs: Minimum number of tab switches per action.
        max_tabs: Maximum number of tab switches per action.
    """

    enabled: bool = False
    weight: float = 5.0
    context_aware: bool = True
    backward_chance: float = 0.3
    min_tabs: int = 1
    max_tabs: int = 4

    def __post_init__(self) -> None:
        self.weight = max(0.0, self.weight)
        self.backward_chance = max(0.0, min(1.0, self.backward_chance))
        self.min_tabs = max(1, self.min_tabs)
        self.max_tabs = max(self.min_tabs, self.max_tabs)


@dataclass
class CodeTypingConfig:
    """Configuration for the code-typing simulator.

    Attributes:
        enabled: Whether the code-typing simulator is active.
        weight: Relative selection weight among enabled simulators.
        min_chars: Minimum characters to type per action.
        max_chars: Maximum characters to type per action.
        char_delay_min: Minimum delay in seconds between keystrokes.
        char_delay_max: Maximum delay in seconds between keystrokes.
        source_file: Path to a text file to read snippets from.
            When empty, built-in code snippets are used.
    """

    enabled: bool = False
    weight: float = 20.0
    min_chars: int = 10
    max_chars: int = 60
    char_delay_min: float = 0.05
    char_delay_max: float = 0.15
    source_file: str = ""

    def __post_init__(self) -> None:
        self.weight = max(0.0, self.weight)
        self.min_chars = max(1, self.min_chars)
        self.max_chars = max(self.min_chars, self.max_chars)
        self.char_delay_min = max(0.01, self.char_delay_min)
        self.char_delay_max = max(self.char_delay_min, self.char_delay_max)


@dataclass
class HotkeyConfig:
    """Global hotkey bindings for runtime control.

    Attributes:
        toggle: Key combination to pause/resume simulation.
        quit: Key combination to quit the application.
        hide_tray: Key combination to hide the system-tray icon.
    """

    toggle: str = "<ctrl>+<alt>+s"
    quit: str = "<ctrl>+<alt>+q"
    hide_tray: str = "<ctrl>+<alt>+h"
    code_typing: str = "<ctrl>+<alt>+t"


@dataclass
class StealthConfig:
    """Stealth and anti-detection settings.

    Attributes:
        rename_process: Whether to rename the running process.
        process_name: Name to use when process renaming is enabled.
        hide_tray: Whether to hide the system-tray icon on startup.
    """

    rename_process: bool = True
    process_name: str = "system_service"
    hide_tray: bool = False


@dataclass
class PhantomConfig:
    """Top-level configuration aggregating all subsystem configs.

    Attributes:
        timing: Timing and interval parameters.
        mouse: Mouse-movement simulator settings.
        keyboard: Keyboard simulator settings.
        scroll: Scroll-wheel simulator settings.
        app_switcher: Application-switcher simulator settings.
        browser_tabs: Browser-tab switching simulator settings.
        code_typing: Code-typing simulator settings.
        hotkeys: Global hotkey bindings.
        stealth: Stealth and anti-detection settings.
    """

    timing: TimingConfig = field(default_factory=TimingConfig)
    mouse: MouseConfig = field(default_factory=MouseConfig)
    keyboard: KeyboardConfig = field(default_factory=KeyboardConfig)
    scroll: ScrollConfig = field(default_factory=ScrollConfig)
    app_switcher: AppSwitcherConfig = field(default_factory=AppSwitcherConfig)
    browser_tabs: BrowserTabsConfig = field(default_factory=BrowserTabsConfig)
    code_typing: CodeTypingConfig = field(default_factory=CodeTypingConfig)
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
        if self.code_typing.enabled:
            sims["code_typing"] = self.code_typing.weight
        return sims
