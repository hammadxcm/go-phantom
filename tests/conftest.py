"""Shared fixtures for phantom tests."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from phantom.config.schema import (
    AppSwitcherConfig,
    BrowserTabsConfig,
    KeyboardConfig,
    MouseConfig,
    PhantomConfig,
    ScrollConfig,
)


@pytest.fixture
def default_config():
    return PhantomConfig()


@pytest.fixture
def config_lock():
    return threading.Lock()


@pytest.fixture
def mouse_config():
    return MouseConfig()


@pytest.fixture
def keyboard_config():
    return KeyboardConfig()


@pytest.fixture
def scroll_config():
    return ScrollConfig()


@pytest.fixture
def app_switcher_config():
    return AppSwitcherConfig()


@pytest.fixture
def browser_tabs_config():
    return BrowserTabsConfig()
