"""Predefined configuration profiles."""

from __future__ import annotations

import logging

from phantom.config.schema import PhantomConfig
from phantom.constants import ALL_SIMULATORS_SET

log = logging.getLogger(__name__)

#: Mapping of preset name to override configuration dicts.
#: Each entry may contain a ``_only`` key (set of enabled simulators)
#: and section-level overrides (e.g. ``"timing"``, ``"mouse"``).
PRESETS: dict[str, dict] = {
    "default": {
        "_only": {"mouse", "keyboard", "scroll"},
        "timing": {"interval_mean": 8.0, "interval_stddev": 4.0},
    },
    "aggressive": {
        "_only": {"mouse", "keyboard", "scroll", "app_switcher", "browser_tabs"},
        "timing": {"interval_mean": 3.0, "interval_stddev": 1.5},
    },
    "stealth": {
        "_only": {"mouse", "scroll"},
        "timing": {"interval_mean": 15.0, "interval_stddev": 5.0},
        "mouse": {"min_distance": 20, "max_distance": 150},
    },
    "minimal": {
        "_only": {"mouse"},
        "timing": {"interval_mean": 20.0, "interval_stddev": 6.0},
    },
    "presentation": {
        "_only": {"mouse", "scroll"},
        "timing": {"interval_mean": 5.0, "interval_stddev": 2.0},
    },
}

#: Ordered list of available preset names.
PRESET_NAMES: list[str] = list(PRESETS.keys())


def apply_preset(config: PhantomConfig, name: str) -> None:
    """Apply a named preset profile to the config in-place.

    Enables/disables simulators and overrides timing or simulator
    settings according to the preset definition.

    Args:
        config: Configuration instance to mutate.
        name: Preset name (must exist in ``PRESETS``).

    Raises:
        ValueError: If *name* is not a recognized preset.
    """
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name!r}. Available: {PRESET_NAMES}")

    preset = PRESETS[name]

    # Handle simulator selection
    if "_only" in preset:
        enabled = preset["_only"]
        for sim in ALL_SIMULATORS_SET:
            getattr(config, sim).enabled = sim in enabled

    # Apply section overrides
    for section, values in preset.items():
        if section.startswith("_"):
            continue
        if isinstance(values, dict):
            sub = getattr(config, section, None)
            if sub is None:
                log.warning("Preset %r references unknown config section: %s", name, section)
                continue
            for key, value in values.items():
                if hasattr(sub, key):
                    setattr(sub, key, value)
                else:
                    log.warning("Preset %r references unknown key: %s.%s", name, section, key)
