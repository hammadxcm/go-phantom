"""Tests for phantom.simulators registry."""

from __future__ import annotations

import pytest

from phantom.simulators import (
    SIMULATOR_REGISTRY,
    create_simulators,
    register_simulator,
)
from phantom.simulators.base import BaseSimulator


class FakeSim(BaseSimulator):
    def execute(self, config):
        pass


class TestSimulatorRegistry:
    def test_default_registry_has_all_sims(self):
        expected = {"mouse", "keyboard", "scroll", "app_switcher", "browser_tabs", "code_typing"}
        assert expected <= set(SIMULATOR_REGISTRY.keys())

    def test_create_simulators_returns_instances(self):
        sims = create_simulators()
        assert len(sims) >= 6
        for name, sim in sims.items():
            assert isinstance(sim, BaseSimulator), f"{name} is not a BaseSimulator"

    def test_register_custom_simulator(self):
        register_simulator("fake", FakeSim)
        assert "fake" in SIMULATOR_REGISTRY
        sims = create_simulators()
        assert isinstance(sims["fake"], FakeSim)
        # Cleanup
        del SIMULATOR_REGISTRY["fake"]

    def test_register_non_simulator_raises(self):
        with pytest.raises(TypeError, match="must be a subclass"):
            register_simulator("bad", dict)  # type: ignore[arg-type]

    def test_register_overwrites_existing(self):
        original = SIMULATOR_REGISTRY["mouse"]
        register_simulator("mouse", FakeSim)
        assert SIMULATOR_REGISTRY["mouse"] is FakeSim
        # Restore
        SIMULATOR_REGISTRY["mouse"] = original
