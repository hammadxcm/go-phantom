#!/usr/bin/env bash
# Phantom installer — works on macOS, Linux, and Windows (Git Bash / WSL / MSYS2)
# Usage: curl -fsSL <raw-url>/install.sh | bash
#   or:  ./install.sh

set -euo pipefail

# ─── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# ─── Helpers ──────────────────────────────────────────────────────────────────
info()    { printf "${BLUE}[INFO]${RESET}  %s\n" "$1"; }
success() { printf "${GREEN}[OK]${RESET}    %s\n" "$1"; }
warn()    { printf "${YELLOW}[WARN]${RESET}  %s\n" "$1"; }
error()   { printf "${RED}[ERROR]${RESET} %s\n" "$1" >&2; exit 1; }
step()    { printf "\n${CYAN}${BOLD}▸ %s${RESET}\n" "$1"; }

# ─── Banner ───────────────────────────────────────────────────────────────────
printf "\n"
printf "${BOLD}${CYAN}"
printf "  ╔═══════════════════════════════════════╗\n"
printf "  ║         Phantom Installer v1.0        ║\n"
printf "  ║   Cross-platform activity simulator   ║\n"
printf "  ╚═══════════════════════════════════════╝\n"
printf "${RESET}\n"

# ─── OS Detection ─────────────────────────────────────────────────────────────
step "Detecting platform"
RAW_OS="$(uname -s)"
ARCH="$(uname -m)"

case "$RAW_OS" in
    Darwin)
        PLATFORM="macOS"
        HOME_DIR="$HOME"
        ;;
    Linux)
        PLATFORM="Linux"
        HOME_DIR="$HOME"
        # Check if running inside WSL
        if grep -qi microsoft /proc/version 2>/dev/null; then
            PLATFORM="Linux (WSL)"
        fi
        ;;
    MINGW*|MSYS*|CYGWIN*)
        PLATFORM="Windows (Git Bash)"
        HOME_DIR="$USERPROFILE"
        if [ -z "$HOME_DIR" ]; then
            HOME_DIR="$HOME"
        fi
        ;;
    *)
        error "Unsupported OS: $RAW_OS"
        ;;
esac
info "Platform: $PLATFORM ($ARCH)"

# ─── Paths (OS-aware) ────────────────────────────────────────────────────────
INSTALL_DIR="${PHANTOM_INSTALL_DIR:-$HOME_DIR/.phantom}"
case "$RAW_OS" in
    MINGW*|MSYS*|CYGWIN*)
        BIN_DIR="${PHANTOM_BIN_DIR:-$HOME_DIR/.local/bin}"
        VENV_ACTIVATE="Scripts/activate"
        VENV_PYTHON="Scripts/python"
        ;;
    *)
        BIN_DIR="${PHANTOM_BIN_DIR:-$HOME_DIR/.local/bin}"
        VENV_ACTIVATE="bin/activate"
        VENV_PYTHON="bin/python"
        ;;
esac

# ─── Platform-specific checks ────────────────────────────────────────────────
if [ "$PLATFORM" = "Linux" ]; then
    SESSION_TYPE="${XDG_SESSION_TYPE:-unknown}"
    if [ "$SESSION_TYPE" = "wayland" ]; then
        error "Wayland detected. Phantom requires X11.

  Switch to an X11/Xorg session at your login screen:
    GNOME: Select 'GNOME on Xorg' or 'Ubuntu on Xorg'
    KDE:   Select 'Plasma (X11)'"
    fi
    if [ "$SESSION_TYPE" = "x11" ]; then
        success "X11 session confirmed"
    else
        warn "Could not detect session type (XDG_SESSION_TYPE=$SESSION_TYPE). Phantom requires X11."
    fi
fi

if [ "$PLATFORM" = "Linux (WSL)" ]; then
    warn "Running in WSL. Phantom needs a display server."
    info "Make sure you have an X11 server running (VcXsrv, X410, or WSLg)."
    if [ -z "${DISPLAY:-}" ]; then
        warn "DISPLAY is not set. Export it: export DISPLAY=:0"
    fi
fi

# ─── Python Check ─────────────────────────────────────────────────────────────
step "Checking Python"
PYTHON=""
for cmd in python3 python py; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        major=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "0")
        minor=$("$cmd" -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "0")
        if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    printf "\n"
    case "$RAW_OS" in
        Darwin)
            error "Python 3.8+ is required.

  Install with Homebrew:
    brew install python" ;;
        MINGW*|MSYS*|CYGWIN*)
            error "Python 3.8+ is required.

  Install from: https://www.python.org/downloads/
  IMPORTANT: Check 'Add Python to PATH' during installation.

  Or with winget:
    winget install Python.Python.3.12" ;;
        *)
            error "Python 3.8+ is required.

  Install Python:
    Ubuntu/Debian: sudo apt install python3 python3-venv
    Fedora:        sudo dnf install python3
    Arch:          sudo pacman -S python" ;;
    esac
fi
success "Found $PYTHON ($version)"

# ─── Check venv module ────────────────────────────────────────────────────────
if ! "$PYTHON" -c "import venv" &>/dev/null; then
    case "$RAW_OS" in
        Darwin)
            error "Python venv module not found. Reinstall Python: brew install python" ;;
        MINGW*|MSYS*|CYGWIN*)
            error "Python venv module not found. Reinstall Python from python.org (ensure 'pip' is checked)." ;;
        *)
            error "Python venv module not found.

  Install it:
    Ubuntu/Debian: sudo apt install python3-venv
    Fedora:        sudo dnf install python3-devel
    Arch:          (included with python package)" ;;
    esac
fi

# ─── Install project files ───────────────────────────────────────────────────
step "Installing Phantom to $INSTALL_DIR"
if [ -d "$INSTALL_DIR/phantom" ]; then
    info "Existing installation found, updating..."
    if [ -d "$INSTALL_DIR/.git" ]; then
        git -C "$INSTALL_DIR" pull --quiet 2>/dev/null || true
        success "Updated from git"
    else
        success "Using existing installation"
    fi
else
    mkdir -p "$INSTALL_DIR"
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
    if [ -f "$SCRIPT_DIR/pyproject.toml" ] && [ -d "$SCRIPT_DIR/phantom" ]; then
        cp -r "$SCRIPT_DIR/phantom" "$INSTALL_DIR/"
        cp "$SCRIPT_DIR/pyproject.toml" "$INSTALL_DIR/"
        cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true
        [ -f "$SCRIPT_DIR/Makefile" ] && cp "$SCRIPT_DIR/Makefile" "$INSTALL_DIR/"
        success "Copied project files"
    else
        error "Cannot find project files. Run this script from the phantom repo root."
    fi
fi

# ─── Virtual environment ──────────────────────────────────────────────────────
step "Setting up virtual environment"
VENV_DIR="$INSTALL_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    info "Virtual environment already exists"
else
    "$PYTHON" -m venv "$VENV_DIR"
    success "Created virtual environment"
fi

# Activate and install
source "$VENV_DIR/$VENV_ACTIVATE"
pip install --quiet --upgrade pip 2>/dev/null
pip install --quiet -e "$INSTALL_DIR" 2>&1 | tail -1
success "Dependencies installed"

# ─── Create launcher scripts ─────────────────────────────────────────────────
step "Creating phantom command"
mkdir -p "$BIN_DIR"

case "$RAW_OS" in
    MINGW*|MSYS*|CYGWIN*)
        # Windows: create .cmd for CMD and .ps1 for PowerShell
        cat > "$BIN_DIR/phantom.cmd" << LAUNCHER
@echo off
call "$VENV_DIR\\Scripts\\activate.bat"
python -m phantom %*
LAUNCHER

        cat > "$BIN_DIR/phantom.ps1" << LAUNCHER
& "$VENV_DIR\\Scripts\\Activate.ps1"
python -m phantom @args
LAUNCHER

        # Also create a bash launcher for Git Bash
        cat > "$BIN_DIR/phantom" << LAUNCHER
#!/usr/bin/env bash
source "$VENV_DIR/$VENV_ACTIVATE"
exec python -m phantom "\$@"
LAUNCHER
        chmod +x "$BIN_DIR/phantom"

        success "Created $BIN_DIR/phantom.cmd  (Command Prompt)"
        success "Created $BIN_DIR/phantom.ps1  (PowerShell)"
        success "Created $BIN_DIR/phantom      (Git Bash)"
        ;;
    *)
        # macOS / Linux: bash launcher
        cat > "$BIN_DIR/phantom" << LAUNCHER
#!/usr/bin/env bash
source "$VENV_DIR/$VENV_ACTIVATE"
exec python -m phantom "\$@"
LAUNCHER
        chmod +x "$BIN_DIR/phantom"
        success "Created $BIN_DIR/phantom"
        ;;
esac

# ─── PATH check ───────────────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    warn "$BIN_DIR is not in your PATH"
    printf "\n"

    case "$RAW_OS" in
        MINGW*|MSYS*|CYGWIN*)
            info "Add to Windows PATH (run in PowerShell as admin):"
            printf "\n"
            printf "  ${DIM}[Environment]::SetEnvironmentVariable('PATH', '%s;' + [Environment]::GetEnvironmentVariable('PATH', 'User'), 'User')${RESET}\n" "$BIN_DIR"
            ;;
        *)
            info "Add it to your shell profile:"
            printf "\n"
            SHELL_NAME="$(basename "${SHELL:-bash}")"
            case "$SHELL_NAME" in
                zsh)  RC_FILE="~/.zshrc" ;;
                bash) RC_FILE="~/.bashrc" ;;
                fish) RC_FILE="~/.config/fish/config.fish" ;;
                *)    RC_FILE="~/.profile" ;;
            esac

            if [ "$SHELL_NAME" = "fish" ]; then
                printf "  ${DIM}echo 'set -gx PATH \$PATH %s' >> %s${RESET}\n" "$BIN_DIR" "$RC_FILE"
            else
                printf "  ${DIM}echo 'export PATH=\"%s:\$PATH\"' >> %s${RESET}\n" "$BIN_DIR" "$RC_FILE"
            fi
            printf "\n"
            info "Then restart your terminal or run: source $RC_FILE"
            ;;
    esac
fi

# ─── Platform-specific post-install notes ─────────────────────────────────────
case "$PLATFORM" in
    macOS)
        printf "\n"
        printf "${YELLOW}${BOLD}  ⚠  macOS Accessibility Permission Required${RESET}\n"
        printf "\n"
        printf "  ${DIM}System Settings → Privacy & Security → Accessibility${RESET}\n"
        printf "  ${DIM}Enable your terminal app (Terminal, iTerm2, etc.)${RESET}\n"
        ;;
    "Windows (Git Bash)")
        printf "\n"
        printf "${YELLOW}${BOLD}  ⚠  Windows Defender may flag Phantom${RESET}\n"
        printf "\n"
        printf "  ${DIM}Windows Security → Virus & threat protection → Exclusions${RESET}\n"
        printf "  ${DIM}Add folder: $INSTALL_DIR${RESET}\n"
        ;;
    "Linux (WSL)")
        printf "\n"
        printf "${YELLOW}${BOLD}  ⚠  WSL requires an X11 display server${RESET}\n"
        printf "\n"
        printf "  ${DIM}Install WSLg (Windows 11) or VcXsrv/X410 (Windows 10)${RESET}\n"
        printf "  ${DIM}export DISPLAY=:0  # Add to ~/.bashrc${RESET}\n"
        ;;
esac

# ─── Done ─────────────────────────────────────────────────────────────────────
printf "\n"
printf "${GREEN}${BOLD}  ✓ Phantom installed successfully!${RESET}\n"
printf "\n"
printf "  ${BOLD}Quick start:${RESET}\n"
printf "    ${DIM}phantom${RESET}                    Run with defaults\n"
printf "    ${DIM}phantom -v${RESET}                 Run with debug logging\n"
printf "    ${DIM}phantom -c config.json${RESET}     Custom config\n"
printf "\n"
printf "  ${BOLD}Hotkeys:${RESET}\n"
printf "    ${DIM}Ctrl+Alt+S${RESET}   Start / Pause\n"
printf "    ${DIM}Ctrl+Alt+Q${RESET}   Quit\n"
printf "    ${DIM}Ctrl+Alt+H${RESET}   Hide tray icon\n"
printf "\n"
printf "  ${BOLD}Uninstall:${RESET}\n"
printf "    ${DIM}rm -rf ~/.phantom ~/.local/bin/phantom${RESET}\n"
printf "\n"
