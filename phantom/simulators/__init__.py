"""Activity simulators."""

from phantom.simulators.app_switcher import AppSwitcherSimulator
from phantom.simulators.base import BaseSimulator
from phantom.simulators.browser_tabs import BrowserTabsSimulator
from phantom.simulators.keyboard import KeyboardSimulator
from phantom.simulators.mouse import MouseSimulator
from phantom.simulators.scroll import ScrollSimulator

__all__ = [
    "AppSwitcherSimulator",
    "BaseSimulator",
    "BrowserTabsSimulator",
    "KeyboardSimulator",
    "MouseSimulator",
    "ScrollSimulator",
]
