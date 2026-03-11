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
- **Target Python**: 3.8+
- **Type hints**: use them for function signatures

Before committing, run:

```bash
make lint      # Check for issues
make format    # Auto-format code
```

### Testing

All tests must pass before submitting a PR:

```bash
pytest                      # Run all tests
pytest --cov=phantom        # With coverage report
```

- Maintain or improve test coverage (currently 99%)
- Add tests for new functionality
- Tests live in `tests/` and follow the `test_*.py` naming convention

### Running locally

```bash
python -m phantom           # Normal mode
python -m phantom -v        # Verbose/debug logging
python -m phantom -c config.json  # Custom config
```

## Pull Request Process

1. **Describe your changes** — what and why, not just how
2. **Link related issues** if applicable
3. **One feature per PR** — keep changes focused
4. **Squash commits** into logical units before requesting review
5. Ensure `make lint` passes with no warnings
6. Ensure all tests pass

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
├── __main__.py          # CLI entry point, argument parsing
├── app.py               # Main application orchestrator
├── config/
│   ├── defaults.json    # Default configuration values
│   ├── manager.py       # Config loading/saving/resolution
│   └── schema.py        # Dataclass definitions for config
├── core/
│   ├── platform.py      # OS detection utilities
│   ├── randomization.py # Weighted random, jitter, distributions
│   └── scheduler.py     # Main simulation loop
├── hotkeys/
│   └── manager.py       # Global hotkey registration (pynput)
├── simulators/
│   ├── base.py          # Abstract BaseSimulator class
│   ├── mouse.py         # Bezier curve mouse movement
│   ├── keyboard.py      # Modifier-key keyboard simulation
│   ├── scroll.py        # Scroll wheel simulation
│   ├── app_switcher.py  # Alt+Tab / Cmd+Tab simulation
│   └── browser_tabs.py  # Ctrl+Tab browser tab switching
├── stealth/
│   ├── anti_detection.py # Timing jitter, pattern avoidance
│   └── process.py        # Process name masking
└── ui/
    ├── icons.py          # Tray icon generation
    └── tray.py           # System tray integration (pystray)
```

**Key patterns:**
- All simulators extend `BaseSimulator` and implement `execute(config)`
- Simulator selection uses weighted random based on config weights
- Config is loaded as dataclasses defined in `config/schema.py`
- Platform-specific behavior is isolated in `core/platform.py`

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold its standards.
