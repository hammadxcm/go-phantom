"""Tests for phantom.ui.gui."""

from __future__ import annotations

import sys
import threading
from unittest.mock import MagicMock, patch

from phantom.config.schema import PhantomConfig
from phantom.core.stats import Stats


def _make_mock_root():
    """Create a mock Tk root with all needed attributes."""
    mock_root = MagicMock()
    mock_root.after = MagicMock()
    mock_root.title = MagicMock()
    mock_root.geometry = MagicMock()
    mock_root.configure = MagicMock()
    mock_root.resizable = MagicMock()
    mock_root.protocol = MagicMock()
    mock_root.iconphoto = MagicMock()
    mock_root.destroy = MagicMock()
    mock_root.withdraw = MagicMock()
    mock_root.mainloop = MagicMock()
    return mock_root


def _make_var(value):
    """Create a MagicMock that behaves like a tk variable."""
    return MagicMock(
        get=MagicMock(return_value=value),
        set=MagicMock(),
    )


import pytest  # noqa: E402


@pytest.fixture
def gui_module():
    """Import gui module with tk/ttk mocked."""
    mock_tk = MagicMock()
    mock_root = _make_mock_root()
    mock_tk.Tk.return_value = mock_root
    mock_tk.BOTH = "both"
    mock_tk.X = "x"
    mock_tk.W = "w"
    mock_tk.LEFT = "left"
    mock_tk.RIGHT = "right"
    mock_tk.HORIZONTAL = "horizontal"
    mock_tk.BooleanVar = MagicMock(
        side_effect=lambda **kw: _make_var(kw.get("value", False)),
    )
    mock_tk.DoubleVar = MagicMock(
        side_effect=lambda **kw: _make_var(kw.get("value", 0.0)),
    )
    mock_tk.StringVar = MagicMock(
        side_effect=lambda **kw: _make_var(kw.get("value", "")),
    )

    mock_ttk = MagicMock()
    mock_ttk.Style.return_value = MagicMock()

    with patch.dict(sys.modules, {"tkinter": mock_tk, "tkinter.ttk": mock_ttk}):
        # Remove cached gui module if present
        sys.modules.pop("phantom.ui.gui", None)
        import phantom.ui.gui as gui_mod

        yield gui_mod, mock_root
        sys.modules.pop("phantom.ui.gui", None)


def _make_gui(gui_module_fixture):
    """Create a PhantomGUI instance from the mocked module."""
    gui_mod, mock_root = gui_module_fixture
    on_toggle = MagicMock(return_value=True)
    on_quit = MagicMock()
    on_save = MagicMock()

    gui = gui_mod.PhantomGUI(
        stats=Stats(),
        config=PhantomConfig(),
        config_lock=threading.Lock(),
        on_toggle=on_toggle,
        on_quit=on_quit,
        on_save_config=on_save,
    )
    return gui, on_toggle, on_quit, on_save, mock_root


class TestPhantomGUIInit:
    def test_creates_window(self, gui_module):
        _gui, _, _, _, mock_root = _make_gui(gui_module)
        mock_root.title.assert_called_with("Phantom")
        mock_root.geometry.assert_called_with("500x640")
        mock_root.resizable.assert_called_with(False, False)

    def test_icon_fallback_no_crash(self, gui_module):
        """When ImageTk is unavailable, GUI still initializes (fallback path)."""
        gui, _, _, _, _mock_root = _make_gui(gui_module)
        # The try/except block catches ImportError — GUI should still work
        assert gui is not None

    def test_icon_try_block_exists_in_source(self):
        """Verify the iconphoto code path exists in gui.py source."""
        from pathlib import Path

        src = (Path(__file__).parent.parent / "phantom" / "ui" / "gui.py").read_text()
        assert "iconphoto" in src
        assert "create_tray_icon" in src
        assert "ImageTk" in src

    def test_with_preset_name(self, gui_module):
        gui_mod, _mock_root = gui_module
        gui = gui_mod.PhantomGUI(
            stats=Stats(),
            config=PhantomConfig(),
            config_lock=threading.Lock(),
            on_toggle=MagicMock(return_value=True),
            on_quit=MagicMock(),
            on_save_config=MagicMock(),
            preset_name="stealth",
        )
        assert gui._preset_name == "stealth"

    def test_default_preset_name(self, gui_module):
        gui, _, _, _, _ = _make_gui(gui_module)
        assert gui._preset_name == "default"


class TestPhantomGUICallbacks:
    def test_toggle_click(self, gui_module):
        gui, on_toggle, _, _, _ = _make_gui(gui_module)
        gui._on_toggle_click()
        on_toggle.assert_called_once()

    def test_save_click(self, gui_module):
        gui, _, _, on_save, _ = _make_gui(gui_module)
        gui._on_save_click()
        on_save.assert_called_once()

    def test_quit_click(self, gui_module):
        gui, _, on_quit, _, mock_root = _make_gui(gui_module)
        gui._on_quit_click()
        on_quit.assert_called_once()
        mock_root.destroy.assert_called_once()

    def test_close_withdraws(self, gui_module):
        gui, _, _, _, mock_root = _make_gui(gui_module)
        gui._on_close()
        mock_root.withdraw.assert_called_once()

    def test_run_calls_mainloop(self, gui_module):
        gui, _, _, _, mock_root = _make_gui(gui_module)
        gui.run()
        mock_root.mainloop.assert_called_once()


class TestPhantomGUIConfigUpdate:
    def test_sim_enabled_changed(self, gui_module):
        gui_mod, _mock_root = gui_module
        config = PhantomConfig()
        gui = gui_mod.PhantomGUI(
            stats=Stats(),
            config=config,
            config_lock=threading.Lock(),
            on_toggle=MagicMock(return_value=True),
            on_quit=MagicMock(),
            on_save_config=MagicMock(),
        )
        gui._sim_vars["mouse"].get.return_value = False
        gui._on_sim_enabled_changed("mouse")
        assert config.mouse.enabled is False

    def test_weight_changed(self, gui_module):
        gui_mod, _mock_root = gui_module
        config = PhantomConfig()
        gui = gui_mod.PhantomGUI(
            stats=Stats(),
            config=config,
            config_lock=threading.Lock(),
            on_toggle=MagicMock(return_value=True),
            on_quit=MagicMock(),
            on_save_config=MagicMock(),
        )
        gui._sim_weight_vars["mouse"].get.return_value = 75.0
        gui._on_weight_changed("mouse")
        assert config.mouse.weight == 75.0

    def test_timing_changed(self, gui_module):
        gui_mod, _mock_root = gui_module
        config = PhantomConfig()
        gui = gui_mod.PhantomGUI(
            stats=Stats(),
            config=config,
            config_lock=threading.Lock(),
            on_toggle=MagicMock(return_value=True),
            on_quit=MagicMock(),
            on_save_config=MagicMock(),
        )
        gui._timing_vars["interval_mean"].get.return_value = 5.0
        gui._on_timing_changed("interval_mean")
        assert config.timing.interval_mean == 5.0
