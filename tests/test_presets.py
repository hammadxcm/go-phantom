"""Tests for phantom.config.presets."""

from __future__ import annotations

import pytest

from phantom.config.presets import PRESET_NAMES, apply_preset
from phantom.config.schema import PhantomConfig


class TestApplyPreset:
    def test_apply_default_preset(self):
        cfg = PhantomConfig()
        apply_preset(cfg, "default")
        assert cfg.mouse.enabled is True
        assert cfg.keyboard.enabled is True
        assert cfg.scroll.enabled is True
        assert cfg.app_switcher.enabled is False
        assert cfg.browser_tabs.enabled is False

    def test_apply_aggressive_preset(self):
        cfg = PhantomConfig()
        apply_preset(cfg, "aggressive")
        assert cfg.mouse.enabled is True
        assert cfg.keyboard.enabled is True
        assert cfg.scroll.enabled is True
        assert cfg.app_switcher.enabled is True
        assert cfg.browser_tabs.enabled is True
        assert cfg.timing.interval_mean == 3.0

    def test_apply_stealth_preset(self):
        cfg = PhantomConfig()
        apply_preset(cfg, "stealth")
        assert cfg.mouse.enabled is True
        assert cfg.scroll.enabled is True
        assert cfg.keyboard.enabled is False
        assert cfg.app_switcher.enabled is False
        assert cfg.browser_tabs.enabled is False
        assert cfg.timing.interval_mean == 15.0

    def test_apply_minimal_preset(self):
        cfg = PhantomConfig()
        apply_preset(cfg, "minimal")
        assert cfg.mouse.enabled is True
        assert cfg.keyboard.enabled is False
        assert cfg.scroll.enabled is False
        assert cfg.app_switcher.enabled is False
        assert cfg.browser_tabs.enabled is False

    def test_apply_presentation_preset(self):
        cfg = PhantomConfig()
        apply_preset(cfg, "presentation")
        assert cfg.mouse.enabled is True
        assert cfg.scroll.enabled is True
        assert cfg.keyboard.enabled is False
        assert cfg.app_switcher.enabled is False
        assert cfg.browser_tabs.enabled is False
        assert cfg.timing.interval_mean == 5.0
        assert cfg.timing.interval_stddev == 2.0

    def test_apply_unknown_preset_raises(self):
        cfg = PhantomConfig()
        with pytest.raises(ValueError, match="Unknown preset"):
            apply_preset(cfg, "nonexistent")

    def test_preset_names_list(self):
        assert PRESET_NAMES == ["default", "aggressive", "stealth", "minimal", "presentation"]

    def test_preset_overrides_timing_values(self):
        cfg = PhantomConfig()
        # Default timing is 8.0 mean, 4.0 stddev
        assert cfg.timing.interval_mean == 8.0
        apply_preset(cfg, "aggressive")
        assert cfg.timing.interval_mean == 3.0
        assert cfg.timing.interval_stddev == 1.5

    def test_preset_overrides_mouse_config(self):
        cfg = PhantomConfig()
        # Default mouse distances
        assert cfg.mouse.min_distance == 50
        assert cfg.mouse.max_distance == 500
        apply_preset(cfg, "stealth")
        assert cfg.mouse.min_distance == 20
        assert cfg.mouse.max_distance == 150
