# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-03-11

### Added

- **Mouse simulator** with Bezier curve movement and micro-corrections
- **Keyboard simulator** using modifier-key-only presses
- **Scroll simulator** with configurable click range
- **App switcher simulator** (Cmd+Tab on macOS, Alt+Tab on Windows/Linux)
- **Browser tabs simulator** (Ctrl+Tab switching)
- **Weighted random scheduler** with normal distribution timing and idle periods
- **Global hotkeys** via pynput (toggle, quit, hide tray — all configurable)
- **System tray integration** with start/pause/quit menu
- **Stealth features**: process name masking (`setproctitle`), tray icon hiding, anti-detection timing jitter
- **JSON configuration** with layered resolution (executable dir → cwd → `~/.phantom/`)
- **CLI interface** with `-c` (config path) and `-v` (verbose logging) flags
- **Cross-platform support** for macOS, Windows, and Linux (X11)
- **PyInstaller build** for single-file executable distribution
- **TUI dashboard** (`--tui` flag) with real-time stats, live logs, and toggle status panels via `rich.live`
- **Rich logging** with colored output, timestamps, and tracebacks
- **Stats tracking layer** — thread-safe metrics collector tracking actions, uptime, and pause counts
- **DequeHandler** — bounded log handler for TUI log display
- **GitHub Actions CI** — lint + test on every push/PR
- **GitHub Actions release workflow** — automated builds for macOS (arm64), Linux (x86_64), and Windows (.exe)
- **GitHub Actions PyPI publishing** — automated sdist + wheel publishing on tag push
- **Homebrew formula** for macOS installation (`brew install hammadxcm/go-phantom/phantom`)
- **.deb packaging** via `fpm` in CI for Linux distribution
- **PyPI metadata** — classifiers, URLs, license, and readme for `pipx install go-phantom`
- 202 tests at 99% coverage
