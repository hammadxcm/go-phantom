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
    CodeTypingConfig,
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
    "code_typing": CodeTypingConfig,
    "hotkeys": HotkeyConfig,
    "stealth": StealthConfig,
}


class ConfigManager:
    """Thread-safe configuration loader and saver.

    Searches for ``config.json`` beside the executable or in
    ``~/.phantom/``, deserializes it into a ``PhantomConfig``
    dataclass, and supports live updates and persistence.
    """

    CONFIG_FILENAME = "config.json"

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize the manager and load configuration from disk.

        Args:
            config_path: Explicit path to a JSON config file. When
                ``None``, the default resolution order is used.
        """
        self._lock = threading.Lock()
        self._path = Path(config_path) if config_path else self._resolve_path()
        self._config = self._load()

    @property
    def config(self) -> PhantomConfig:
        """Return the current configuration.

        Returns:
            The active ``PhantomConfig`` instance.
        """
        with self._lock:
            return self._config

    def save(self) -> None:
        """Persist the current configuration to disk as JSON."""
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = asdict(self._config)
            self._path.write_text(json.dumps(data, indent=2))
            log.info("Config saved to %s", self._path)

    def update(self, section: str, **kwargs: Any) -> None:
        """Update a config section with keyword arguments.

        Args:
            section: Top-level config section name (e.g. ``"mouse"``).
            **kwargs: Field names and new values to set.
        """
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
        """Resolve the configuration file path.

        Returns:
            Path beside the executable if it exists, otherwise
            ``~/.phantom/config.json``.
        """
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
        """Load and parse the config file, falling back to defaults.

        Returns:
            A ``PhantomConfig`` populated from disk or with defaults.
        """
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
        """Parse a raw JSON dict into a ``PhantomConfig``.

        Args:
            raw: Deserialized JSON mapping.

        Returns:
            A fully populated ``PhantomConfig`` instance.
        """
        kwargs: dict[str, Any] = {}
        for section_name, cls in _SECTION_MAP.items():
            if section_name in raw and isinstance(raw[section_name], dict):
                # Only pass fields that the dataclass accepts
                valid_fields = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
                filtered = {k: v for k, v in raw[section_name].items() if k in valid_fields}
                kwargs[section_name] = cls(**filtered)
        return PhantomConfig(**kwargs)
