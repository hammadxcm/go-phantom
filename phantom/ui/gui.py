"""Tkinter GUI for Phantom — lightweight, stdlib-only control panel."""

from __future__ import annotations

import threading
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phantom.config.schema import PhantomConfig
    from phantom.core.stats import Stats

import phantom

# Simulator display metadata: (config_attr, label, weight_attr)
_SIMULATORS = [
    ("mouse", "Mouse", "weight"),
    ("keyboard", "Keyboard", "weight"),
    ("scroll", "Scroll", "weight"),
    ("app_switcher", "App Switch", "weight"),
    ("browser_tabs", "Browser", "weight"),
    ("code_typing", "Code Type", "weight"),
]

# Dark theme colours
_BG = "#1e1e2e"
_BG_SECTION = "#282840"
_FG = "#cdd6f4"
_FG_DIM = "#6c7086"
_ACCENT = "#89b4fa"
_GREEN = "#a6e3a1"
_RED = "#f38ba8"
_YELLOW = "#f9e2af"
_SLIDER_TROUGH = "#45475a"


class PhantomGUI:
    """Tkinter-based control panel for Phantom.

    Provides simulator toggles, weight sliders, timing controls, preset
    selection, and live status display — all without extra dependencies.
    """

    def __init__(
        self,
        stats: Stats,
        config: PhantomConfig,
        config_lock: threading.Lock,
        on_toggle: Callable[[], bool],
        on_quit: Callable[[], None],
        on_save_config: Callable[[], None],
        on_sim_pause: Callable[[str], bool] | None = None,
        preset_name: str | None = None,
    ) -> None:
        self._stats = stats
        self._config = config
        self._config_lock = config_lock
        self._on_toggle = on_toggle
        self._on_quit = on_quit
        self._on_save_config = on_save_config
        self._on_sim_pause = on_sim_pause
        self._preset_name = preset_name or "default"
        self._running = True

        self._root = tk.Tk()
        self._root.title("Phantom")
        self._root.geometry("500x640")
        self._root.configure(bg=_BG)
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Set window icon from brand icon
        try:
            from PIL import ImageTk

            from phantom.ui.icons import create_tray_icon

            self._icon_img = create_tray_icon()
            self._icon_photo = ImageTk.PhotoImage(self._icon_img)
            self._root.iconphoto(True, self._icon_photo)  # type: ignore[arg-type]
        except Exception:
            pass  # Non-critical — fall back to default icon

        self._style = ttk.Style(self._root)
        self._configure_theme()

        self._sim_vars: dict[str, tk.BooleanVar] = {}
        self._sim_weight_vars: dict[str, tk.DoubleVar] = {}
        self._sim_weight_labels: dict[str, ttk.Label] = {}
        self._sim_action_labels: dict[str, ttk.Label] = {}

        self._timing_vars: dict[str, tk.DoubleVar] = {}
        self._timing_labels: dict[str, ttk.Label] = {}

        self._build_ui()
        self._refresh()

    # ── Theme ──────────────────────────────────────────────────────────────

    def _configure_theme(self) -> None:
        self._style.theme_use("clam")
        self._style.configure("Dark.TFrame", background=_BG)
        self._style.configure("Section.TFrame", background=_BG_SECTION)
        self._style.configure(
            "Dark.TLabel",
            background=_BG,
            foreground=_FG,
            font=("Segoe UI", 10),
        )
        self._style.configure(
            "Section.TLabel",
            background=_BG_SECTION,
            foreground=_FG,
            font=("Segoe UI", 10),
        )
        self._style.configure(
            "Header.TLabel",
            background=_BG,
            foreground=_ACCENT,
            font=("Segoe UI", 12, "bold"),
        )
        self._style.configure(
            "SectionHeader.TLabel",
            background=_BG_SECTION,
            foreground=_ACCENT,
            font=("Segoe UI", 11, "bold"),
        )
        self._style.configure(
            "Status.TLabel",
            background=_BG,
            foreground=_GREEN,
            font=("Segoe UI", 10, "bold"),
        )
        self._style.configure(
            "Dim.TLabel",
            background=_BG,
            foreground=_FG_DIM,
            font=("Segoe UI", 9),
        )
        self._style.configure(
            "Dark.TCheckbutton",
            background=_BG_SECTION,
            foreground=_FG,
            font=("Segoe UI", 10),
        )
        self._style.map(
            "Dark.TCheckbutton",
            background=[("active", _BG_SECTION)],
        )
        self._style.configure(
            "Dark.Horizontal.TScale",
            background=_BG_SECTION,
            troughcolor=_SLIDER_TROUGH,
        )
        self._style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
        )
        self._style.configure(
            "Dark.TCombobox",
            fieldbackground=_BG_SECTION,
            background=_BG_SECTION,
            foreground=_FG,
        )

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        main = ttk.Frame(self._root, style="Dark.TFrame", padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        self._build_header(main)
        self._build_preset_bar(main)
        self._build_simulators_section(main)
        self._build_timing_section(main)
        self._build_buttons(main)

    def _build_header(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text=f"Phantom v{phantom.__version__}",
            style="Header.TLabel",
        ).pack(anchor=tk.W)

        status_frame = ttk.Frame(parent, style="Dark.TFrame")
        status_frame.pack(fill=tk.X, pady=(4, 0))

        self._status_label = ttk.Label(
            status_frame,
            text="\u25cf RUNNING",
            style="Status.TLabel",
        )
        self._status_label.pack(side=tk.LEFT)

        self._uptime_label = ttk.Label(
            status_frame,
            text="Uptime: 00:00",
            style="Dim.TLabel",
        )
        self._uptime_label.pack(side=tk.LEFT, padx=(16, 0))

        self._actions_label = ttk.Label(
            status_frame,
            text="Actions: 0",
            style="Dim.TLabel",
        )
        self._actions_label.pack(side=tk.LEFT, padx=(16, 0))

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

    def _build_preset_bar(self, parent: ttk.Frame) -> None:
        from phantom.config.presets import PRESET_NAMES

        bar = ttk.Frame(parent, style="Dark.TFrame")
        bar.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(bar, text="Preset:", style="Dark.TLabel").pack(side=tk.LEFT)

        self._preset_var = tk.StringVar(value=self._preset_name)
        combo = ttk.Combobox(
            bar,
            textvariable=self._preset_var,
            values=PRESET_NAMES,
            state="readonly",
            width=14,
            style="Dark.TCombobox",
        )
        combo.pack(side=tk.LEFT, padx=(8, 8))

        ttk.Button(
            bar,
            text="Apply",
            command=self._apply_preset,
            style="Accent.TButton",
        ).pack(side=tk.LEFT)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

    def _build_simulators_section(self, parent: ttk.Frame) -> None:
        section = ttk.Frame(parent, style="Section.TFrame", padding=10)
        section.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(section, text="Simulators", style="SectionHeader.TLabel").pack(
            anchor=tk.W, pady=(0, 6)
        )

        for attr, label, _ in _SIMULATORS:
            sim_cfg = getattr(self._config, attr)
            row = ttk.Frame(section, style="Section.TFrame")
            row.pack(fill=tk.X, pady=2)

            var = tk.BooleanVar(value=sim_cfg.enabled)
            self._sim_vars[attr] = var
            cb = ttk.Checkbutton(
                row,
                text=f"{label:<12}",
                variable=var,
                style="Dark.TCheckbutton",
                command=lambda a=attr: self._on_sim_enabled_changed(a),  # type: ignore[misc]
            )
            cb.pack(side=tk.LEFT)

            weight_var = tk.DoubleVar(value=sim_cfg.weight)
            self._sim_weight_vars[attr] = weight_var
            slider = ttk.Scale(
                row,
                from_=0,
                to=100,
                variable=weight_var,
                orient=tk.HORIZONTAL,
                length=180,
                style="Dark.Horizontal.TScale",
            )
            slider.pack(side=tk.LEFT, padx=(4, 4))
            slider.bind(
                "<ButtonRelease-1>",
                lambda e, a=attr: self._on_weight_changed(a),  # type: ignore[misc]
            )

            wt_label = ttk.Label(
                row,
                text=f"{sim_cfg.weight:>5.0f}",
                style="Section.TLabel",
                width=5,
            )
            wt_label.pack(side=tk.LEFT)
            self._sim_weight_labels[attr] = wt_label

            act_label = ttk.Label(
                row,
                text="[0]",
                style="Section.TLabel",
                width=6,
            )
            act_label.pack(side=tk.LEFT, padx=(4, 0))
            self._sim_action_labels[attr] = act_label

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

    def _build_timing_section(self, parent: ttk.Frame) -> None:
        section = ttk.Frame(parent, style="Section.TFrame", padding=10)
        section.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(section, text="Timing", style="SectionHeader.TLabel").pack(
            anchor=tk.W, pady=(0, 6)
        )

        timing_defs = [
            ("interval_mean", "Interval Mean", 0.5, 30.0, "s"),
            ("interval_stddev", "Interval Stddev", 0.0, 15.0, "s"),
            ("idle_chance", "Idle Chance", 0.0, 1.0, "%"),
        ]

        for attr, label, lo, hi, unit in timing_defs:
            row = ttk.Frame(section, style="Section.TFrame")
            row.pack(fill=tk.X, pady=2)

            ttk.Label(row, text=f"{label:<18}", style="Section.TLabel").pack(side=tk.LEFT)

            val = getattr(self._config.timing, attr)
            var = tk.DoubleVar(value=val)
            self._timing_vars[attr] = var

            slider = ttk.Scale(
                row,
                from_=lo,
                to=hi,
                variable=var,
                orient=tk.HORIZONTAL,
                length=180,
                style="Dark.Horizontal.TScale",
            )
            slider.pack(side=tk.LEFT, padx=(4, 4))
            slider.bind(
                "<ButtonRelease-1>",
                lambda e, a=attr: self._on_timing_changed(a),  # type: ignore[misc]
            )

            display = f"{val * 100:>5.0f}%" if unit == "%" else f"{val:>5.1f}{unit}"
            t_label = ttk.Label(row, text=display, style="Section.TLabel", width=8)
            t_label.pack(side=tk.LEFT)
            self._timing_labels[attr] = t_label

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

    def _build_buttons(self, parent: ttk.Frame) -> None:
        bar = ttk.Frame(parent, style="Dark.TFrame")
        bar.pack(fill=tk.X, pady=(4, 0))

        self._toggle_btn = ttk.Button(
            bar,
            text="\u23f8 Pause",
            command=self._on_toggle_click,
            style="Accent.TButton",
            width=12,
        )
        self._toggle_btn.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            bar,
            text="Save",
            command=self._on_save_click,
            style="Accent.TButton",
            width=10,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            bar,
            text="Quit",
            command=self._on_quit_click,
            style="Accent.TButton",
            width=10,
        ).pack(side=tk.RIGHT)

    # ── Refresh loop ──────────────────────────────────────────────────────

    def _refresh(self) -> None:
        snap = self._stats.snapshot()

        # Status
        active = snap.get("active", True)
        if active:
            self._status_label.configure(text="\u25cf RUNNING", foreground=_GREEN)
            self._toggle_btn.configure(text="\u23f8 Pause")
        else:
            self._status_label.configure(text="\u25cf PAUSED", foreground=_YELLOW)
            self._toggle_btn.configure(text="\u25b6 Start")
        self._running = active

        # Uptime
        uptime = int(snap.get("uptime", 0))
        mins, secs = divmod(uptime, 60)
        hrs, mins = divmod(mins, 60)
        if hrs:
            self._uptime_label.configure(text=f"Uptime: {hrs:d}:{mins:02d}:{secs:02d}")
        else:
            self._uptime_label.configure(text=f"Uptime: {mins:02d}:{secs:02d}")

        # Total actions
        total = snap.get("total_actions", 0)
        self._actions_label.configure(text=f"Actions: {total}")

        # Per-simulator action counts
        by_sim = snap.get("actions_by_simulator", {})
        for attr, _, _ in _SIMULATORS:
            count = by_sim.get(attr, 0)
            if attr in self._sim_action_labels:
                self._sim_action_labels[attr].configure(text=f"[{count}]")

        # Update weight labels from slider values
        for attr in self._sim_weight_vars:
            val = self._sim_weight_vars[attr].get()
            self._sim_weight_labels[attr].configure(text=f"{val:>5.0f}")

        # Update timing labels
        for attr in self._timing_vars:
            val = self._timing_vars[attr].get()
            if attr == "idle_chance":
                self._timing_labels[attr].configure(text=f"{val * 100:>5.0f}%")
            else:
                self._timing_labels[attr].configure(text=f"{val:>5.1f}s")

        self._root.after(500, self._refresh)

    # ── Callbacks ─────────────────────────────────────────────────────────

    def _on_sim_enabled_changed(self, attr: str) -> None:
        enabled = self._sim_vars[attr].get()
        with self._config_lock:
            getattr(self._config, attr).enabled = enabled

    def _on_weight_changed(self, attr: str) -> None:
        val = self._sim_weight_vars[attr].get()
        with self._config_lock:
            getattr(self._config, attr).weight = val

    def _on_timing_changed(self, attr: str) -> None:
        val = self._timing_vars[attr].get()
        with self._config_lock:
            setattr(self._config.timing, attr, val)

    def _on_toggle_click(self) -> None:
        self._on_toggle()

    def _on_save_click(self) -> None:
        self._on_save_config()

    def _on_quit_click(self) -> None:
        self._on_quit()
        self._root.destroy()

    def _on_close(self) -> None:
        """Window X button: hide to tray, keep simulation running."""
        self._root.withdraw()

    def _apply_preset(self) -> None:
        from phantom.config.presets import apply_preset

        name = self._preset_var.get()
        with self._config_lock:
            apply_preset(self._config, name)

        # Update all GUI controls to match new config
        for attr, _, _ in _SIMULATORS:
            sim_cfg = getattr(self._config, attr)
            self._sim_vars[attr].set(sim_cfg.enabled)
            self._sim_weight_vars[attr].set(sim_cfg.weight)

        for attr in self._timing_vars:
            self._timing_vars[attr].set(getattr(self._config.timing, attr))

        self._preset_name = name

    # ── Public API ────────────────────────────────────────────────────────

    def run(self) -> None:
        """Enter the tkinter mainloop (must run on main thread)."""
        self._root.mainloop()
