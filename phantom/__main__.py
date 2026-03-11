"""Entry point for `python -m phantom`."""

from __future__ import annotations

import argparse
import logging
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="phantom",
        description="Cross-platform activity simulator",
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to config.json",
        default=None,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch TUI dashboard (mutually exclusive with system tray)",
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO

    log_handler = None
    if args.tui:
        from phantom.ui.log_handler import DequeHandler

        log_handler = DequeHandler(maxlen=200)
        log_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
        handlers: list[logging.Handler] = [log_handler]
        logging.basicConfig(
            level=level, format="%(message)s", datefmt="%H:%M:%S", handlers=handlers,
        )
    else:
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

    # Suppress noisy library loggers
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pynput").setLevel(logging.WARNING)

    from phantom.app import PhantomApp

    app = PhantomApp(config_path=args.config)
    try:
        app.run(tui=args.tui, log_handler=log_handler)
    except KeyboardInterrupt:
        logging.info("Interrupted")
        sys.exit(0)


if __name__ == "__main__":
    main()
