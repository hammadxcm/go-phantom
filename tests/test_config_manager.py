"""Tests for phantom.config.manager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from phantom.config.manager import ConfigManager
from phantom.config.schema import PhantomConfig


class TestConfigManagerResolve:
    def test_loads_defaults_when_no_file(self, tmp_path):
        cm = ConfigManager(config_path=str(tmp_path / "nonexistent.json"))
        assert isinstance(cm.config, PhantomConfig)
        assert cm.config.mouse.enabled is True

    def test_loads_from_file(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({
            "mouse": {"enabled": False, "weight": 10.0},
            "keyboard": {"max_presses": 5},
        }))
        cm = ConfigManager(config_path=str(cfg_file))
        assert cm.config.mouse.enabled is False
        assert cm.config.mouse.weight == 10.0
        assert cm.config.keyboard.max_presses == 5
        # Unmodified sections keep defaults
        assert cm.config.scroll.enabled is True

    def test_handles_invalid_json(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text("not json{{{")
        cm = ConfigManager(config_path=str(cfg_file))
        # Should fall back to defaults
        assert cm.config.mouse.enabled is True

    def test_handles_unknown_fields(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({
            "mouse": {"enabled": True, "unknown_field": 999},
        }))
        cm = ConfigManager(config_path=str(cfg_file))
        assert cm.config.mouse.enabled is True

    def test_handles_non_dict_section(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({
            "mouse": "not a dict",
            "keyboard": {"max_presses": 7},
        }))
        cm = ConfigManager(config_path=str(cfg_file))
        # mouse should be default, keyboard should be parsed
        assert cm.config.mouse.enabled is True
        assert cm.config.keyboard.max_presses == 7


class TestConfigManagerSave:
    def test_save_creates_file(self, tmp_path):
        cfg_file = tmp_path / "subdir" / "config.json"
        cm = ConfigManager(config_path=str(cfg_file))
        cm.save()
        assert cfg_file.exists()
        data = json.loads(cfg_file.read_text())
        assert data["mouse"]["enabled"] is True

    def test_save_roundtrip(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cm = ConfigManager(config_path=str(cfg_file))
        cm.update("mouse", weight=77.0)
        cm.save()

        cm2 = ConfigManager(config_path=str(cfg_file))
        assert cm2.config.mouse.weight == 77.0


class TestConfigManagerUpdate:
    def test_update_valid_field(self, tmp_path):
        cm = ConfigManager(config_path=str(tmp_path / "c.json"))
        cm.update("mouse", enabled=False, weight=5.0)
        assert cm.config.mouse.enabled is False
        assert cm.config.mouse.weight == 5.0

    def test_update_unknown_section(self, tmp_path):
        cm = ConfigManager(config_path=str(tmp_path / "c.json"))
        cm.update("nonexistent", foo=1)  # Should not raise

    def test_update_unknown_key(self, tmp_path):
        cm = ConfigManager(config_path=str(tmp_path / "c.json"))
        cm.update("mouse", nonexistent_key=42)  # Should not raise
        assert cm.config.mouse.enabled is True  # Unchanged


class TestConfigManagerResolvePath:
    def test_resolve_uses_cwd_by_default(self):
        cm = ConfigManager()
        # Should resolve without error
        assert cm._path is not None

    def test_resolve_frozen(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sys.frozen", True, raising=False)
        monkeypatch.setattr("sys.executable", str(tmp_path / "phantom"))
        cm = ConfigManager()
        # Should not crash
        assert cm._path is not None

    def test_resolve_home_fallback(self, tmp_path, monkeypatch):
        # Make sure no config.json exists in cwd
        monkeypatch.chdir(tmp_path)
        home_dir = tmp_path / ".phantom"
        home_dir.mkdir()
        cfg = home_dir / "config.json"
        cfg.write_text(json.dumps({"mouse": {"weight": 22.0}}))
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        cm = ConfigManager()
        assert cm.config.mouse.weight == 22.0

    def test_resolve_cwd_config_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps({"mouse": {"weight": 55.0}}))
        cm = ConfigManager()
        assert cm._path == cfg
        assert cm.config.mouse.weight == 55.0
