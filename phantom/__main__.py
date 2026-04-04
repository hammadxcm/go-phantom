"""Entry point for `python -m phantom`."""

from __future__ import annotations

import argparse
import logging
import sys

from phantom.constants import ALL_SIMULATORS_SET


def _has_console() -> bool:
    """Return True when stdout and stderr are available."""
    return sys.stdout is not None and sys.stderr is not None


def _warn(msg: str) -> None:
    """Print a warning to stderr if available."""
    if sys.stderr is not None:
        print(msg, file=sys.stderr)


def _setup_file_logging(level: int) -> logging.Handler:
    """Configure and return a RotatingFileHandler to ~/.phantom/phantom.log."""
    from logging.handlers import RotatingFileHandler
    from pathlib import Path

    log_dir = Path.home() / ".phantom"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "phantom.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ),
    )
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="%H:%M:%S",
        handlers=[file_handler],
    )
    return file_handler


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Returns:
        An ``argparse.ArgumentParser`` configured with all phantom
        sub-commands, flags, and option groups.
    """
    parser = argparse.ArgumentParser(
        prog="phantom",
        description="Cross-platform activity simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  phantom                           # run with defaults (mouse + keyboard + scroll)
  phantom --mouse-only              # mouse movement only
  phantom --keyboard-only           # keyboard simulation only
  phantom --only mouse,scroll       # mouse + scroll only
  phantom --enable app_switcher     # add app switcher to defaults
  phantom --disable mouse,keyboard  # disable specific simulators
  phantom --interval 3.0            # faster action interval (default: 8s)
  phantom --idle-chance 0            # no idle pauses
  phantom --stealth                 # max stealth (rename process + hide tray)
  phantom --no-stealth              # disable all stealth features
  phantom --tui                     # TUI dashboard mode
  phantom --tail                    # streaming colored log mode
  phantom --ghost                   # silent mode, logs to file only
  phantom -c myconfig.json          # load custom config file
""",
    )

    # ─── Core options ────────────────────────────────────────────────────────
    parser.add_argument(
        "-c",
        "--config",
        help="Path to config.json",
        default=None,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    # ─── Output mode (mutually exclusive) ─────────────────────────────────
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--tui",
        action="store_true",
        help="Launch TUI dashboard (mutually exclusive with --tail/--ghost)",
    )
    mode_group.add_argument(
        "--tail",
        action="store_true",
        help="Streaming colored logs like tail -f",
    )
    mode_group.add_argument(
        "--ghost",
        action="store_true",
        help="Zero terminal output, logs to ~/.phantom/phantom.log",
    )
    mode_group.add_argument(
        "--gui",
        action="store_true",
        help="Launch tkinter GUI window (default on Windows without console)",
    )

    parser.add_argument(
        "--preset",
        metavar="NAME",
        choices=["default", "aggressive", "stealth", "minimal", "presentation"],
        help="Load a preset profile (default, aggressive, stealth, minimal, presentation)",
    )

    # ─── Simulator selection ─────────────────────────────────────────────────
    sim_group = parser.add_argument_group("simulator selection")
    sim_group.add_argument(
        "--mouse-only",
        action="store_true",
        help="Run mouse simulator only",
    )
    sim_group.add_argument(
        "--keyboard-only",
        action="store_true",
        help="Run keyboard simulator only",
    )
    sim_group.add_argument(
        "--scroll-only",
        action="store_true",
        help="Run scroll simulator only",
    )
    sim_group.add_argument(
        "--only",
        metavar="SIMS",
        help="Simulators to enable: mouse,keyboard,scroll,app_switcher,browser_tabs",
    )
    sim_group.add_argument(
        "--enable",
        metavar="SIMS",
        help="Comma-separated list of simulators to enable (added to defaults)",
    )
    sim_group.add_argument(
        "--disable",
        metavar="SIMS",
        help="Comma-separated list of simulators to disable",
    )
    sim_group.add_argument(
        "--all",
        action="store_true",
        help="Enable all simulators (including app_switcher and browser_tabs)",
    )

    # ─── Timing overrides ────────────────────────────────────────────────────
    timing_group = parser.add_argument_group("timing")
    timing_group.add_argument(
        "--interval",
        type=float,
        metavar="SECONDS",
        help="Mean interval between actions (default: 8.0)",
    )
    timing_group.add_argument(
        "--interval-stddev",
        type=float,
        metavar="SECONDS",
        help="Standard deviation of interval (default: 4.0)",
    )
    timing_group.add_argument(
        "--idle-chance",
        type=float,
        metavar="PROB",
        help="Probability of idle pause per cycle, 0-1 (default: 0.10)",
    )

    # ─── Simulator tuning ────────────────────────────────────────────────────
    tuning_group = parser.add_argument_group("simulator tuning")
    tuning_group.add_argument(
        "--mouse-distance",
        type=int,
        nargs=2,
        metavar=("MIN", "MAX"),
        help="Mouse movement distance range in pixels (default: 50 500)",
    )
    tuning_group.add_argument(
        "--mouse-speed",
        type=int,
        metavar="STEPS",
        help="Bezier curve steps — higher = smoother/slower (default: 100)",
    )
    tuning_group.add_argument(
        "--key-presses",
        type=int,
        metavar="MAX",
        help="Max modifier key presses per action (default: 3)",
    )
    tuning_group.add_argument(
        "--scroll-clicks",
        type=int,
        nargs=2,
        metavar=("MIN", "MAX"),
        help="Scroll click range per action (default: 1 5)",
    )
    tuning_group.add_argument(
        "--capslock-chance",
        type=float,
        metavar="PROB",
        help="CapsLock double-tap probability, 0-1 (default: 0.15)",
    )
    tuning_group.add_argument(
        "--horizontal-scroll-chance",
        type=float,
        metavar="PROB",
        help="Horizontal scroll probability, 0-1 (default: 0.1)",
    )
    tuning_group.add_argument(
        "--app-switcher-tabs",
        type=int,
        nargs=2,
        metavar=("MIN", "MAX"),
        help="App switcher tab range (default: 1 3)",
    )
    tuning_group.add_argument(
        "--browser-tabs-count",
        type=int,
        nargs=2,
        metavar=("MIN", "MAX"),
        help="Browser tabs switch count range (default: 1 4)",
    )
    tuning_group.add_argument(
        "--code-typing-chars",
        type=int,
        nargs=2,
        metavar=("MIN", "MAX"),
        help="Code typing character count range (default: 10 60)",
    )
    tuning_group.add_argument(
        "--code-typing-file",
        metavar="PATH",
        help="Text file to read typing snippets from (one per line)",
    )

    # ─── Weight overrides ────────────────────────────────────────────────────
    weight_group = parser.add_argument_group("weights (higher = more frequent)")
    weight_group.add_argument(
        "--mouse-weight",
        type=float,
        metavar="W",
        help="Mouse weight (default: 40)",
    )
    weight_group.add_argument(
        "--keyboard-weight",
        type=float,
        metavar="W",
        help="Keyboard weight (default: 30)",
    )
    weight_group.add_argument(
        "--scroll-weight",
        type=float,
        metavar="W",
        help="Scroll weight (default: 15)",
    )
    weight_group.add_argument(
        "--app-switcher-weight",
        type=float,
        metavar="W",
        help="App switcher weight (default: 10)",
    )
    weight_group.add_argument(
        "--browser-tabs-weight",
        type=float,
        metavar="W",
        help="Browser tabs weight (default: 5)",
    )
    weight_group.add_argument(
        "--code-typing-weight",
        type=float,
        metavar="W",
        help="Code typing weight (default: 20)",
    )

    # ─── Stealth ─────────────────────────────────────────────────────────────
    stealth_group = parser.add_argument_group("stealth")
    stealth_group.add_argument(
        "--stealth",
        action="store_true",
        help="Max stealth: rename process + hide tray icon",
    )
    stealth_group.add_argument(
        "--no-stealth",
        action="store_true",
        help="Disable all stealth features",
    )
    stealth_group.add_argument(
        "--process-name",
        metavar="NAME",
        help="Custom process name for masking (default: system_service)",
    )

    # ─── Hotkeys ─────────────────────────────────────────────────────────────
    hotkey_group = parser.add_argument_group("hotkeys")
    hotkey_group.add_argument(
        "--hotkey-toggle",
        metavar="KEYS",
        help="Toggle hotkey (default: <ctrl>+<alt>+s)",
    )
    hotkey_group.add_argument(
        "--hotkey-quit",
        metavar="KEYS",
        help="Quit hotkey (default: <ctrl>+<alt>+q)",
    )
    hotkey_group.add_argument(
        "--hotkey-hide",
        metavar="KEYS",
        help="Hide tray hotkey (default: <ctrl>+<alt>+h)",
    )
    hotkey_group.add_argument(
        "--hotkey-code-typing",
        metavar="KEYS",
        help="Code typing toggle hotkey (default: <ctrl>+<alt>+t)",
    )

    return parser


def _apply_sim_selection(args: argparse.Namespace, overrides: dict) -> None:
    """Apply simulator selection flags to the overrides dict.

    Processes ``--mouse-only``, ``--keyboard-only``, ``--scroll-only``,
    ``--only``, ``--all``, ``--enable``, and ``--disable`` flags.  Unknown
    simulator names are reported to stderr and silently ignored.

    Args:
        args: Parsed CLI namespace.
        overrides: Mutable dict that accumulates config overrides.
    """
    if args.mouse_only:
        overrides["_only"] = {"mouse"}
    elif args.keyboard_only:
        overrides["_only"] = {"keyboard"}
    elif args.scroll_only:
        overrides["_only"] = {"scroll"}
    elif args.only:
        user_set = {s.strip() for s in args.only.split(",")}
        unknown = user_set - ALL_SIMULATORS_SET
        if unknown:
            names = ", ".join(sorted(unknown))
            _warn(f"Warning: unknown simulators ignored: {names}")
        overrides["_only"] = user_set & ALL_SIMULATORS_SET
    elif getattr(args, "all", False):
        overrides["_only"] = set(ALL_SIMULATORS_SET)

    if args.enable:
        user_set = {s.strip() for s in args.enable.split(",")}
        unknown = user_set - ALL_SIMULATORS_SET
        if unknown:
            names = ", ".join(sorted(unknown))
            _warn(f"Warning: unknown simulators ignored: {names}")
        overrides["_enable"] = user_set & ALL_SIMULATORS_SET
    if args.disable:
        user_set = {s.strip() for s in args.disable.split(",")}
        unknown = user_set - ALL_SIMULATORS_SET
        if unknown:
            names = ", ".join(sorted(unknown))
            _warn(f"Warning: unknown simulators ignored: {names}")
        overrides["_disable"] = user_set & ALL_SIMULATORS_SET


def _apply_timing_overrides(args: argparse.Namespace, overrides: dict) -> None:
    """Apply timing-related CLI flags to the overrides dict.

    Handles ``--interval``, ``--interval-stddev``, and ``--idle-chance``.

    Args:
        args: Parsed CLI namespace.
        overrides: Mutable dict that accumulates config overrides.
    """
    if args.interval is not None:
        overrides.setdefault("timing", {})["interval_mean"] = args.interval
    if args.interval_stddev is not None:
        overrides.setdefault("timing", {})["interval_stddev"] = args.interval_stddev
    if args.idle_chance is not None:
        overrides.setdefault("timing", {})["idle_chance"] = args.idle_chance


def _apply_tuning_overrides(args: argparse.Namespace, overrides: dict) -> None:
    """Apply simulator tuning flags to the overrides dict.

    Handles ``--mouse-distance``, ``--mouse-speed``, ``--key-presses``, and
    ``--scroll-clicks``.

    Args:
        args: Parsed CLI namespace.
        overrides: Mutable dict that accumulates config overrides.
    """
    if args.mouse_distance:
        overrides.setdefault("mouse", {})["min_distance"] = args.mouse_distance[0]
        overrides["mouse"]["max_distance"] = args.mouse_distance[1]
    if args.mouse_speed is not None:
        overrides.setdefault("mouse", {})["bezier_steps"] = args.mouse_speed
    if args.key_presses is not None:
        overrides.setdefault("keyboard", {})["max_presses"] = args.key_presses
    if args.scroll_clicks:
        overrides.setdefault("scroll", {})["min_clicks"] = args.scroll_clicks[0]
        overrides["scroll"]["max_clicks"] = args.scroll_clicks[1]
    if args.capslock_chance is not None:
        overrides.setdefault("keyboard", {})["capslock_chance"] = args.capslock_chance
    if args.horizontal_scroll_chance is not None:
        overrides.setdefault("scroll", {})["horizontal_chance"] = args.horizontal_scroll_chance
    if args.app_switcher_tabs:
        overrides.setdefault("app_switcher", {})["min_tabs"] = args.app_switcher_tabs[0]
        overrides["app_switcher"]["max_tabs"] = args.app_switcher_tabs[1]
    if args.browser_tabs_count:
        overrides.setdefault("browser_tabs", {})["min_tabs"] = args.browser_tabs_count[0]
        overrides["browser_tabs"]["max_tabs"] = args.browser_tabs_count[1]
    if args.code_typing_chars:
        overrides.setdefault("code_typing", {})["min_chars"] = args.code_typing_chars[0]
        overrides["code_typing"]["max_chars"] = args.code_typing_chars[1]
    if args.code_typing_file:
        overrides.setdefault("code_typing", {})["source_file"] = args.code_typing_file


def _apply_weight_overrides(args: argparse.Namespace, overrides: dict) -> None:
    """Apply simulator weight flags to the overrides dict.

    Handles ``--mouse-weight``, ``--keyboard-weight``, ``--scroll-weight``,
    ``--app-switcher-weight``, and ``--browser-tabs-weight``.

    Args:
        args: Parsed CLI namespace.
        overrides: Mutable dict that accumulates config overrides.
    """
    if args.mouse_weight is not None:
        overrides.setdefault("mouse", {})["weight"] = args.mouse_weight
    if args.keyboard_weight is not None:
        overrides.setdefault("keyboard", {})["weight"] = args.keyboard_weight
    if args.scroll_weight is not None:
        overrides.setdefault("scroll", {})["weight"] = args.scroll_weight
    if args.app_switcher_weight is not None:
        overrides.setdefault("app_switcher", {})["weight"] = args.app_switcher_weight
    if args.browser_tabs_weight is not None:
        overrides.setdefault("browser_tabs", {})["weight"] = args.browser_tabs_weight
    if args.code_typing_weight is not None:
        overrides.setdefault("code_typing", {})["weight"] = args.code_typing_weight


def _apply_stealth_overrides(args: argparse.Namespace, overrides: dict) -> None:
    """Apply stealth-related CLI flags to the overrides dict.

    Handles ``--stealth``, ``--no-stealth``, and ``--process-name``.

    Args:
        args: Parsed CLI namespace.
        overrides: Mutable dict that accumulates config overrides.
    """
    if args.stealth:
        overrides["stealth"] = {"rename_process": True, "hide_tray": True}
    elif args.no_stealth:
        overrides["stealth"] = {"rename_process": False, "hide_tray": False}
    if args.process_name:
        overrides.setdefault("stealth", {})["process_name"] = args.process_name


def _apply_hotkey_overrides(args: argparse.Namespace, overrides: dict) -> None:
    """Apply hotkey CLI flags to the overrides dict.

    Handles ``--hotkey-toggle``, ``--hotkey-quit``, and ``--hotkey-hide``.

    Args:
        args: Parsed CLI namespace.
        overrides: Mutable dict that accumulates config overrides.
    """
    if args.hotkey_toggle:
        overrides.setdefault("hotkeys", {})["toggle"] = args.hotkey_toggle
    if args.hotkey_quit:
        overrides.setdefault("hotkeys", {})["quit"] = args.hotkey_quit
    if args.hotkey_hide:
        overrides.setdefault("hotkeys", {})["hide_tray"] = args.hotkey_hide
    if args.hotkey_code_typing:
        overrides.setdefault("hotkeys", {})["code_typing"] = args.hotkey_code_typing


def _apply_cli_overrides(args: argparse.Namespace) -> dict:
    """Build a config override dict from all CLI arguments.

    Delegates to per-category helpers for simulator selection, timing,
    tuning, weights, stealth, and hotkey flags.

    Args:
        args: Parsed CLI namespace.

    Returns:
        A dict of config overrides ready to pass to ``PhantomApp``.
    """
    overrides: dict = {}
    _apply_sim_selection(args, overrides)
    _apply_timing_overrides(args, overrides)
    _apply_tuning_overrides(args, overrides)
    _apply_weight_overrides(args, overrides)
    _apply_stealth_overrides(args, overrides)
    _apply_hotkey_overrides(args, overrides)
    return overrides


def _resolve_mode(args: argparse.Namespace):
    """Resolve CLI flags to an ``OutputMode`` enum value.

    Checks ``--tui``, ``--tail``, ``--ghost``, and ``--gui`` flags in
    order.  When no flag is given, auto-selects GUI on Windows without a
    console and falls back to TRAY otherwise.

    Args:
        args: Parsed CLI namespace.

    Returns:
        The ``OutputMode`` corresponding to the selected output flag.
    """
    from phantom.ui.modes import OutputMode

    if args.tui:
        return OutputMode.TUI
    if args.tail:
        return OutputMode.TAIL
    if args.ghost:
        return OutputMode.GHOST
    if args.gui:
        return OutputMode.GUI
    # Auto-select GUI on Windows when there is no console
    if sys.platform == "win32" and not _has_console():
        return OutputMode.GUI
    return OutputMode.TRAY


def main() -> None:
    """Entry point for the ``phantom`` CLI.

    Parses arguments, validates ranges, configures logging based on the
    selected output mode, and starts the ``PhantomApp`` run loop.
    """
    parser = _build_parser()
    args = parser.parse_args()

    # Range validation
    if args.interval is not None and args.interval < 0.01:
        parser.error("--interval must be >= 0.01")
    if args.idle_chance is not None and not (0.0 <= args.idle_chance <= 1.0):
        parser.error("--idle-chance must be between 0.0 and 1.0")
    if args.mouse_distance and args.mouse_distance[0] > args.mouse_distance[1]:
        parser.error("--mouse-distance MIN must be <= MAX")
    if args.scroll_clicks and args.scroll_clicks[0] > args.scroll_clicks[1]:
        parser.error("--scroll-clicks MIN must be <= MAX")
    if args.capslock_chance is not None and not (0.0 <= args.capslock_chance <= 1.0):
        parser.error("--capslock-chance must be between 0.0 and 1.0")
    if args.horizontal_scroll_chance is not None and not (
        0.0 <= args.horizontal_scroll_chance <= 1.0
    ):
        parser.error("--horizontal-scroll-chance must be between 0.0 and 1.0")
    if args.app_switcher_tabs and args.app_switcher_tabs[0] > args.app_switcher_tabs[1]:
        parser.error("--app-switcher-tabs MIN must be <= MAX")
    if args.browser_tabs_count and args.browser_tabs_count[0] > args.browser_tabs_count[1]:
        parser.error("--browser-tabs-count MIN must be <= MAX")
    if args.code_typing_chars and args.code_typing_chars[0] > args.code_typing_chars[1]:
        parser.error("--code-typing-chars MIN must be <= MAX")
    weight_args = [
        args.mouse_weight,
        args.keyboard_weight,
        args.scroll_weight,
        args.app_switcher_weight,
        args.browser_tabs_weight,
        args.code_typing_weight,
    ]
    for w in weight_args:
        if w is not None and w < 0:
            parser.error("Weight values must be >= 0")

    level = logging.DEBUG if args.verbose else logging.INFO
    mode = _resolve_mode(args)

    from phantom.ui.modes import OutputMode

    log_handler = None
    if mode == OutputMode.TUI:
        from phantom.ui.log_handler import DequeHandler

        log_handler = DequeHandler(maxlen=200)
        log_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
        handlers: list[logging.Handler] = [log_handler]
        logging.basicConfig(
            level=level,
            format="%(message)s",
            datefmt="%H:%M:%S",
            handlers=handlers,
        )
    elif mode == OutputMode.TAIL:
        if _has_console():
            from phantom.ui.tail_formatter import TailFormatter

            tail_handler = logging.StreamHandler(sys.stdout)
            tail_handler.setFormatter(TailFormatter())
            handlers = [tail_handler]
            logging.basicConfig(
                level=level,
                format="%(message)s",
                datefmt="%H:%M:%S",
                handlers=handlers,
            )
        else:
            _setup_file_logging(level)
    elif mode in (OutputMode.GHOST, OutputMode.GUI):
        _setup_file_logging(level)
    else:
        if _has_console():
            try:
                from rich.logging import RichHandler

                handlers = [RichHandler(rich_tracebacks=True, show_path=False)]
                logging.basicConfig(
                    level=level,
                    format="%(message)s",
                    datefmt="%H:%M:%S",
                    handlers=handlers,
                )
            except ImportError:
                logging.basicConfig(
                    level=level,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    datefmt="%H:%M:%S",
                )
        else:
            _setup_file_logging(level)

    # Suppress noisy library loggers
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pynput").setLevel(logging.WARNING)

    from phantom.app import PhantomApp

    overrides = _apply_cli_overrides(args)
    app = PhantomApp(
        config_path=args.config,
        cli_overrides=overrides,
        preset=getattr(args, "preset", None),
    )
    try:
        app.run(mode=mode, log_handler=log_handler)
    except KeyboardInterrupt:
        logging.info("Interrupted")
        sys.exit(0)


if __name__ == "__main__":
    main()
