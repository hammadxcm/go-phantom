# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.3] - 2026-04-05

### Added

- **Code typing simulator** — types realistic code snippets character by character with human-like inter-keystroke timing. Includes 50+ built-in snippets across Python, JS/TS, Go, Rust, SQL, shell, Docker, and more. Disabled by default.
- **Source file typing** — `--code-typing-file PATH` reads lines from any text file and types them instead of built-in snippets. Falls back gracefully if file is missing.
- **Code typing hotkey** — `Ctrl+Alt+T` toggles code typing on/off at runtime, configurable via `--hotkey-code-typing`.
- **Real-time detailed event logging** — all simulators now log at INFO level with specific details visible in TUI and tail mode:
  - Mouse: `Mouse (500,400)->(720,350) dist=245px correction=yes`
  - Keyboard: `Keyboard 3 presses: Shift, Ctrl, CapsLock`
  - Scroll: `Scroll 3 clicks (2 vertical, 1 horizontal) direction=down`
  - App Switcher: `App switch 2 tabs via Alt+Tab`
  - Browser Tabs: `Browser tabs 2 forward in Google Chrome`
  - Code Typing: `Code typed 25 chars (snippets.txt): 'const data = await fetch('`
- **Configurable CapsLock chance** — `--capslock-chance PROB` (default 0.15) replaces hardcoded value
- **Configurable horizontal scroll chance** — `--horizontal-scroll-chance PROB` (default 0.1) replaces hardcoded value
- **Configurable app switcher tab range** — `--app-switcher-tabs MIN MAX` (default 1 3) replaces hardcoded values
- **Configurable browser tabs count range** — `--browser-tabs-count MIN MAX` (default 1 4) replaces hardcoded values
- **Configurable code typing character range** — `--code-typing-chars MIN MAX` (default 10 60)
- **Stats detail tracking** — `Stats.record_action()` now accepts a detail string, enabling richer TUI preview pane and per-simulator last-action display
- **TUI preview pane** shows per-simulator last action details from stats instead of parsing log messages

### Changed

- All simulator `execute()` methods now return a detail string (was `None`)
- Simulator logging elevated from DEBUG to INFO level for default visibility
- TUI dashboard supports 6 simulators (keys 1-6) instead of 5
- Aggressive preset now includes code_typing simulator
- Stealth preset reduces horizontal scroll chance to 5%

### Fixed

- **Lazy pyautogui import** — `import pyautogui` moved from module level to `execute()` in mouse, scroll, and app.py. Fixes tkinter/MouseInfo warning on WSL/Windows and prevents import failures in headless environments.
- **Missing textual dependency** in `requirements.txt` — now synced with `pyproject.toml`
- **PyInstaller hidden imports** — added `textual`, `setproctitle`, and `pyautogui` to `phantom.spec` for correct binary packaging
- **CI system dependencies** — Linux CI and release builds now install `python3-tk` and `python3-dev`

## [0.0.1] - 2026-03-11

### Added

- **Context-aware tab switching** — browser tabs simulator detects the active window and sends the correct shortcut for each app/OS combination (Cmd+Shift+] for browsers on macOS, Ctrl+Tab for VS Code everywhere, Ctrl+Shift+Right for kitty, etc.)
- **Active window detection** — cross-platform utility (`phantom/core/active_window.py`) that identifies the foreground app via AppleScript (macOS), ctypes (Windows), or xdotool (Linux/X11), with 0.5s result caching
- **Tab shortcut registry** — maps 10+ app patterns to correct tab-switching shortcuts per OS, with substring matching and fallback to Ctrl+Tab
- **Backward tab switching** — `backward_chance` config option (default 30%) for realistic bidirectional tab navigation
- **`context_aware` toggle** — set `context_aware: false` in browser_tabs config to restore the original blind Ctrl+Tab behavior
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
- 298 tests at 99% coverage
