"""Load and save JSON configuration."""

from __future__ import annotations

import json
import logging
import sys
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Any

from phantom.config.schema import (
    AppSwitcherConfig,
    BrowserTabsConfig,
    HotkeyConfig,
    KeyboardConfig,
    MouseConfig,
    PhantomConfig,
    ScrollConfig,
    StealthConfig,
    TimingConfig,
)

log = logging.getLogger(__name__)

_SECTION_MAP = {
    "timing": TimingConfig,
    "mouse": MouseConfig,
    "keyboard": KeyboardConfig,
    "scroll": ScrollConfig,
    "app_switcher": AppSwitcherConfig,
    "browser_tabs": BrowserTabsConfig,
    "hotkeys": HotkeyConfig,
    "stealth": StealthConfig,
}


class ConfigManager:
    """Thread-safe configuration loader and saver."""

    CONFIG_FILENAME = "config.json"

    def __init__(self, config_path: str | None = None) -> None:
        self._lock = threading.Lock()
        self._path = Path(config_path) if config_path else self._resolve_path()
        self._config = self._load()

    @property
    def config(self) -> PhantomConfig:
        with self._lock:
            return self._config

    def save(self) -> None:
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = asdict(self._config)
            self._path.write_text(json.dumps(data, indent=2))
            log.info("Config saved to %s", self._path)

    def update(self, section: str, **kwargs: Any) -> None:
        """Update a config section with keyword arguments."""
        with self._lock:
            sub = getattr(self._config, section, None)
            if sub is None:
                log.warning("Unknown config section: %s", section)
                return
            for key, value in kwargs.items():
                if hasattr(sub, key):
                    setattr(sub, key, value)
                else:
                    log.warning("Unknown key %s.%s", section, key)

    def _resolve_path(self) -> Path:
        """Find config: beside executable, then ~/.phantom/."""
        exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()

        candidate = exe_dir / self.CONFIG_FILENAME
        if candidate.exists():
            return candidate

        home_dir = Path.home() / ".phantom"
        home_candidate = home_dir / self.CONFIG_FILENAME
        if home_candidate.exists():
            return home_candidate

        return candidate

    def _load(self) -> PhantomConfig:
        if not self._path.exists():
            log.info("No config file found at %s, using defaults", self._path)
            return PhantomConfig()

        try:
            raw: dict[str, Any] = json.loads(self._path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            log.error("Failed to read config %s: %s. Using defaults.", self._path, exc)
            return PhantomConfig()

        return self._parse(raw)

    @staticmethod
    def _parse(raw: dict[str, Any]) -> PhantomConfig:
        kwargs: dict[str, Any] = {}
        for section_name, cls in _SECTION_MAP.items():
            if section_name in raw and isinstance(raw[section_name], dict):
                # Only pass fields that the dataclass accepts
                valid_fields = {f for f in cls.__dataclass_fields__}
                filtered = {k: v for k, v in raw[section_name].items() if k in valid_fields}
                kwargs[section_name] = cls(**filtered)
        return PhantomConfig(**kwargs)
