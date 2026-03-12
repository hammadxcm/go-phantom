# Contributing to Phantom

Thanks for your interest in contributing! This guide will help you get started.

## Getting Started

1. Fork the repository and clone your fork
2. Install development dependencies:
   ```bash
   make dev
   ```
3. Create a branch for your work:
   ```bash
   git checkout -b feature/your-feature-name
   # or: bugfix/description, docs/description
   ```

## Development Workflow

### Code style

- **Linter/formatter**: [ruff](https://docs.astral.sh/ruff/)
- **Line length**: 99 characters
- **Target Python**: 3.10+
- **Type hints**: use them for function signatures
- **Type checker**: [mypy](https://mypy-lang.org/) (enforced in CI)
- **Pre-commit**: optional, install with `pre-commit install`

Before committing, run:

```bash
make lint        # Check for issues
make format      # Auto-format code
make typecheck   # Run mypy
```

### Local Testing

#### Quick start

```bash
make test             # Run all tests (uses pytest defaults from pyproject.toml)
```

#### With coverage

```bash
make test-cov         # Run tests with coverage report + 95% threshold
```

This produces a terminal report showing missing lines. The build fails if coverage drops below 95%.

#### Verbose output

```bash
make test-verbose     # Full tracebacks, verbose test names
```

#### Running specific tests

```bash
# Single file
pytest tests/test_dashboard.py

# Single class
pytest tests/test_dashboard.py::TestDashboardBuild

# Single test
pytest tests/test_dashboard.py::TestDashboardBuild::test_build_layout_returns_layout

# By keyword match
pytest -k "test_handle_key"

# By marker (if applicable)
pytest -m "not slow"
```

#### Full pre-commit check

Run format check, lint, and tests with coverage in one command:

```bash
make check
```

This mirrors what CI runs. If `make check` passes locally, CI will pass too.

#### HTML coverage report

```bash
pytest --cov --cov-report=html
open htmlcov/index.html    # macOS
xdg-open htmlcov/index.html  # Linux
```

#### Test structure

```
tests/
├── conftest.py              # Shared fixtures (config, log_handler, dashboard)
├── test_anti_detection.py   # Anti-detection timing tests
├── test_app.py              # PhantomApp orchestrator tests
├── test_config_manager.py   # Config loading/saving tests
├── test_config_schema.py    # Dataclass schema tests
├── test_dashboard.py        # TUI dashboard tests
├── test_hotkeys.py          # Global hotkey tests
├── test_icons.py            # Tray icon generation tests
├── test_log_handler.py      # DequeHandler tests
├── test_main.py             # CLI entry point tests
├── test_platform.py         # OS detection tests
├── test_process.py          # Process masking tests
├── test_randomization.py    # Weighted random / jitter tests
├── test_scheduler.py        # Simulation loop tests
├── test_simulators.py       # Simulator execute() tests
├── test_stats.py            # Stats/metrics tests
└── test_tray.py             # System tray tests
```

**Shared fixtures** in `conftest.py`:
- `default_config` — fresh `PhantomConfig()`
- `config_lock` — `threading.Lock()`
- `mouse_config`, `keyboard_config`, etc. — per-simulator configs
- `log_handler` — `DequeHandler(maxlen=50)` with message formatter
- `dashboard` — fully wired `Dashboard` instance with mock callbacks

Use these fixtures instead of recreating objects inline.

#### Writing new tests

- Place tests in `tests/test_<module>.py`
- Use fixtures from `conftest.py` where possible
- Mock external dependencies (pynput, pyautogui, pystray) — never simulate real input in tests
- Test public behavior, not implementation details
- Aim for 95%+ coverage on new code

### Running locally

```bash
python -m phantom           # Normal mode (tray icon)
python -m phantom -v        # Verbose/debug logging
python -m phantom --tui     # TUI dashboard mode
python -m phantom --tail    # Streaming colored log mode
python -m phantom --ghost   # Silent mode (logs to file only)
python -m phantom -c config.json  # Custom config
```

## Pull Request Process

1. **Run `make check`** locally before pushing
2. **Describe your changes** — what and why, not just how
3. **Link related issues** if applicable
4. **One feature per PR** — keep changes focused
5. **Squash commits** into logical units before requesting review
6. Ensure `make check` passes with no warnings
7. Ensure all tests pass

## Issue Guidelines

### Bug reports

Please include:

- Operating system and version
- Python version (`python --version`)
- Steps to reproduce the issue
- Expected vs actual behavior
- Relevant log output (run with `-v` for debug logs)

### Feature requests

- Describe the use case — what problem does it solve?
- Suggest an approach if you have one in mind
- Note if you're willing to implement it

## Architecture Overview

```
phantom/
├── __main__.py              # CLI entry point, argument parsing
├── app.py                   # Main application orchestrator
├── constants.py             # Shared constants (ALL_SIMULATORS, etc.)
├── config/
│   ├── defaults.json        # Default configuration values
│   ├── manager.py           # Config loading/saving/resolution
│   ├── schema.py            # Dataclass definitions for config
│   └── presets.py           # Preset profiles (default, aggressive, stealth, etc.)
├── core/
│   ├── platform.py          # OS detection utilities
│   ├── randomization.py     # Weighted random, jitter, distributions
│   ├── scheduler.py         # Main simulation loop
│   └── stats.py             # Thread-safe action metrics
├── hotkeys/
│   └── manager.py           # Global hotkey registration (pynput)
├── simulators/
│   ├── base.py              # Abstract BaseSimulator class
│   ├── mouse.py             # Bezier curve mouse movement
│   ├── keyboard.py          # Modifier-key keyboard simulation
│   ├── scroll.py            # Scroll wheel simulation
│   ├── app_switcher.py      # Alt+Tab / Cmd+Tab simulation
│   └── browser_tabs.py      # Ctrl+Tab browser tab switching
├── stealth/
│   ├── anti_detection.py    # Timing jitter, pattern avoidance
│   └── process.py           # Process name masking
└── ui/
    ├── ansi.py              # ANSI escape codes for terminal output
    ├── dashboard.py         # Rich TUI dashboard
    ├── icons.py             # Tray icon generation
    ├── log_handler.py       # DequeHandler for bounded log capture
    ├── modes.py             # OutputMode enum (TRAY, TUI, TAIL, GHOST)
    ├── tail_formatter.py    # Colored log formatter for tail mode
    ├── themes.py            # Color themes (default, hacker, warm)
    └── tray.py              # System tray integration (pystray)
```

**Key patterns:**
- All simulators extend `BaseSimulator` and implement `execute(config)`
- Simulators are registered in `SIMULATOR_REGISTRY` — use `register_simulator()` to add custom ones
- Simulator selection uses weighted random based on config weights
- Config is loaded as dataclasses defined in `config/schema.py`
- Platform-specific behavior is isolated in `core/platform.py`
- ANSI codes are centralized in `ui/ansi.py`; Rich styles in `ui/themes.py`
- Shared constants live in `constants.py` (single source of truth)
- TUI dashboard works cross-platform (Unix `termios` + Windows `msvcrt`)
- Log handler prunes stale entries by age (default 5 min) in addition to size bounds

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold its standards.
