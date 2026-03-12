"""Shared fixtures for phantom tests."""

from __future__ import annotations

import logging
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
from phantom.core.stats import Stats
from phantom.ui.dashboard import Dashboard
from phantom.ui.log_handler import DequeHandler


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


@pytest.fixture
def log_handler():
    handler = DequeHandler(maxlen=50)
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


@pytest.fixture
def dashboard(default_config, log_handler):
    app = Dashboard(
        stats=Stats(),
        config=default_config,
        log_handler=log_handler,
        on_toggle=MagicMock(return_value=True),
        on_quit=MagicMock(),
    )
    return app
