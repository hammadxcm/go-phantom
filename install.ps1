# Phantom installer — works on Windows, macOS, and Linux (PowerShell Core)
# Usage (Windows):          .\install.ps1
# Usage (macOS/Linux):      pwsh install.ps1
# Usage (remote):           irm <raw-url>/install.ps1 | iex

$ErrorActionPreference = "Stop"

# ─── OS Detection ───────────────────────────────────────────────────────────
$IsWin   = ($PSVersionTable.Platform -eq "Win32NT") -or (-not $PSVersionTable.Platform -and $env:OS -eq "Windows_NT")
$IsMac   = $PSVersionTable.Platform -eq "Unix" -and (uname) -eq "Darwin"
$IsLin   = $PSVersionTable.Platform -eq "Unix" -and (uname) -eq "Linux"

if ($IsWin) {
    $PlatformName = "Windows"
    $HomeDir      = $env:USERPROFILE
    $VenvActivate = "Scripts\Activate.ps1"
    $VenvBin      = "Scripts"
    $PathSep      = ";"
} elseif ($IsMac) {
    $PlatformName = "macOS"
    $HomeDir      = $env:HOME
    $VenvActivate = "bin/Activate.ps1"
    $VenvBin      = "bin"
    $PathSep      = ":"
} elseif ($IsLin) {
    $PlatformName = "Linux"
    $HomeDir      = $env:HOME
    $VenvActivate = "bin/Activate.ps1"
    $VenvBin      = "bin"
    $PathSep      = ":"
} else {
    Write-Host "  [ERROR] Unsupported platform." -ForegroundColor Red
    exit 1
}

# ─── Config ──────────────────────────────────────────────────────────────────
$InstallDir = if ($env:PHANTOM_INSTALL_DIR) { $env:PHANTOM_INSTALL_DIR } else { Join-Path $HomeDir ".phantom" }
$BinDir     = if ($env:PHANTOM_BIN_DIR)     { $env:PHANTOM_BIN_DIR }     else { Join-Path $HomeDir ".local/bin" }

# ─── Helpers ─────────────────────────────────────────────────────────────────
function Write-Info    { param($msg) Write-Host "  [INFO]  $msg" -ForegroundColor Blue }
function Write-Ok      { param($msg) Write-Host "  [OK]    $msg" -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "  [WARN]  $msg" -ForegroundColor Yellow }
function Write-Err     { param($msg) Write-Host "  [ERROR] $msg" -ForegroundColor Red; exit 1 }
function Write-Step    { param($msg) Write-Host "`n  > $msg" -ForegroundColor Cyan }

# ─── Banner ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  +=======================================+" -ForegroundColor Cyan
Write-Host "  |         Phantom Installer v1.0        |" -ForegroundColor Cyan
Write-Host "  |   Cross-platform activity simulator   |" -ForegroundColor Cyan
Write-Host "  +=======================================+" -ForegroundColor Cyan
Write-Host ""

Write-Step "Detecting platform"
$Arch = if ($IsWin) { $env:PROCESSOR_ARCHITECTURE } else { (uname -m) }
Write-Info "Platform: $PlatformName ($Arch)"

# ─── Platform checks ────────────────────────────────────────────────────────
if ($IsLin) {
    $SessionType = $env:XDG_SESSION_TYPE
    if ($SessionType -eq "wayland") {
        Write-Err "Wayland detected. Phantom requires X11.`n`n  Switch to X11/Xorg at your login screen:`n    GNOME: Select 'GNOME on Xorg'`n    KDE:   Select 'Plasma (X11)'"
    } elseif ($SessionType -eq "x11") {
        Write-Ok "X11 session confirmed"
    } else {
        Write-Warn "Could not detect session type. Phantom requires X11."
    }
}

# ─── Python Check ────────────────────────────────────────────────────────────
Write-Step "Checking Python"
$Python = $null
$PyCandidates = if ($IsWin) { @("python", "python3", "py") } else { @("python3", "python") }

foreach ($cmd in $PyCandidates) {
    try {
        $ver   = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        $major = & $cmd -c "import sys; print(sys.version_info.major)" 2>$null
        $minor = & $cmd -c "import sys; print(sys.version_info.minor)" 2>$null
        if ([int]$major -ge 3 -and [int]$minor -ge 8) {
            $Python = $cmd
            break
        }
    } catch { }
}

if (-not $Python) {
    if ($IsWin) {
        Write-Err "Python 3.8+ is required.`n`n  Install from: https://www.python.org/downloads/`n  IMPORTANT: Check 'Add Python to PATH' during installation.`n`n  Or with winget:`n    winget install Python.Python.3.12"
    } elseif ($IsMac) {
        Write-Err "Python 3.8+ is required.`n`n  Install with Homebrew:`n    brew install python"
    } else {
        Write-Err "Python 3.8+ is required.`n`n  Install:`n    Ubuntu: sudo apt install python3 python3-venv`n    Fedora: sudo dnf install python3`n    Arch:   sudo pacman -S python"
    }
}
Write-Ok "Found $Python ($ver)"

# ─── Check venv module ──────────────────────────────────────────────────────
try {
    & $Python -c "import venv" 2>$null
    if ($LASTEXITCODE -ne 0) { throw }
} catch {
    if ($IsWin) {
        Write-Err "Python venv module not found. Reinstall Python from python.org (ensure 'pip' is checked)."
    } elseif ($IsMac) {
        Write-Err "Python venv module not found. Reinstall: brew install python"
    } else {
        Write-Err "Python venv module not found.`n  Ubuntu: sudo apt install python3-venv`n  Fedora: sudo dnf install python3-devel"
    }
}

# ─── Install files ───────────────────────────────────────────────────────────
Write-Step "Installing Phantom to $InstallDir"
$PhantomPkgDir = Join-Path $InstallDir "phantom"

if (-not (Test-Path $PhantomPkgDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

    $ScriptDir = if ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } else { Get-Location }

    $PyprojectPath = Join-Path $ScriptDir "pyproject.toml"
    $PhantomSrcDir = Join-Path $ScriptDir "phantom"

    if ((Test-Path $PyprojectPath) -and (Test-Path $PhantomSrcDir)) {
        Copy-Item -Recurse $PhantomSrcDir $PhantomPkgDir
        Copy-Item $PyprojectPath (Join-Path $InstallDir "pyproject.toml")
        $ReqPath = Join-Path $ScriptDir "requirements.txt"
        if (Test-Path $ReqPath) { Copy-Item $ReqPath (Join-Path $InstallDir "requirements.txt") }
        Write-Ok "Copied project files"
    } else {
        Write-Err "Cannot find project files. Run this script from the phantom repo root."
    }
} else {
    Write-Info "Existing installation found"
}

# ─── Virtual environment ─────────────────────────────────────────────────────
Write-Step "Setting up virtual environment"
$VenvDir = Join-Path $InstallDir ".venv"
if (-not (Test-Path $VenvDir)) {
    & $Python -m venv $VenvDir
    Write-Ok "Created virtual environment"
} else {
    Write-Info "Virtual environment already exists"
}

# Activate and install
$ActivatePath = Join-Path $VenvDir $VenvActivate
& $ActivatePath
pip install --quiet --upgrade pip 2>$null
pip install --quiet -e $InstallDir 2>&1 | Select-Object -Last 1
Write-Ok "Dependencies installed"

# ─── Create launcher scripts ─────────────────────────────────────────────────
Write-Step "Creating phantom command"
New-Item -ItemType Directory -Path $BinDir -Force | Out-Null

if ($IsWin) {
    # Windows: .cmd for Command Prompt
    $CmdLauncher = @"
@echo off
call "$(Join-Path $VenvDir 'Scripts\activate.bat')"
python -m phantom %*
"@
    Set-Content -Path (Join-Path $BinDir "phantom.cmd") -Value $CmdLauncher

    # Windows: .ps1 for PowerShell
    $PsLauncher = @"
& "$(Join-Path $VenvDir $VenvActivate)"
python -m phantom @args
"@
    Set-Content -Path (Join-Path $BinDir "phantom.ps1") -Value $PsLauncher

    Write-Ok "Created $(Join-Path $BinDir 'phantom.cmd')  (Command Prompt)"
    Write-Ok "Created $(Join-Path $BinDir 'phantom.ps1')  (PowerShell)"
} else {
    # macOS / Linux: bash launcher
    $BashLauncher = @"
#!/usr/bin/env bash
source "$(Join-Path $VenvDir $VenvActivate -Replace '\\','/')"
exec python -m phantom "`$@"
"@
    $LauncherPath = Join-Path $BinDir "phantom"
    Set-Content -Path $LauncherPath -Value $BashLauncher
    chmod +x $LauncherPath
    Write-Ok "Created $LauncherPath"
}

# ─── PATH check ──────────────────────────────────────────────────────────────
$InPath = $false
foreach ($p in $env:PATH.Split($PathSep)) {
    if ($p.TrimEnd('/\') -eq $BinDir.TrimEnd('/\')) { $InPath = $true; break }
}

if (-not $InPath) {
    Write-Warn "$BinDir is not in your PATH"
    Write-Host ""

    if ($IsWin) {
        Write-Info "Add it automatically? (Y/n)"
        $response = Read-Host "  "
        if ($response -ne "n" -and $response -ne "N") {
            $UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
            [Environment]::SetEnvironmentVariable("PATH", "$BinDir;$UserPath", "User")
            $env:PATH = "$BinDir;$env:PATH"
            Write-Ok "Added to PATH. Restart your terminal for changes to take effect."
        } else {
            Write-Info "Add it manually in PowerShell:"
            Write-Host "    [Environment]::SetEnvironmentVariable('PATH', '$BinDir;' + [Environment]::GetEnvironmentVariable('PATH', 'User'), 'User')" -ForegroundColor DarkGray
        }
    } else {
        $ShellName = Split-Path -Leaf $env:SHELL
        $RcFile = switch ($ShellName) {
            "zsh"  { "~/.zshrc" }
            "fish" { "~/.config/fish/config.fish" }
            default { "~/.bashrc" }
        }
        Write-Info "Add it to your shell profile:"
        Write-Host "    echo 'export PATH=`"$BinDir`:`$PATH`"' >> $RcFile" -ForegroundColor DarkGray
        Write-Host ""
        Write-Info "Then restart your terminal or run: source $RcFile"
    }
}

# ─── Platform-specific post-install notes ────────────────────────────────────
Write-Host ""
if ($IsMac) {
    Write-Host "  ! macOS Accessibility Permission Required" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "    System Settings > Privacy & Security > Accessibility" -ForegroundColor DarkGray
    Write-Host "    Enable your terminal app (Terminal, iTerm2, etc.)" -ForegroundColor DarkGray
} elseif ($IsWin) {
    Write-Host "  ! Windows Defender may flag Phantom (it simulates input)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "    Windows Security > Virus & threat protection > Exclusions" -ForegroundColor DarkGray
    Write-Host "    Add folder: $InstallDir" -ForegroundColor DarkGray
} elseif ($IsLin) {
    $SessionType = $env:XDG_SESSION_TYPE
    if (-not $SessionType -or $SessionType -ne "x11") {
        Write-Host "  ! Phantom requires X11. Make sure you are on an Xorg session." -ForegroundColor Yellow
    }
}

# ─── Done ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Phantom installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Quick start:" -ForegroundColor White
Write-Host "    phantom                    Run with defaults" -ForegroundColor DarkGray
Write-Host "    phantom -v                 Run with debug logging" -ForegroundColor DarkGray
Write-Host "    phantom -c config.json     Custom config" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Hotkeys:" -ForegroundColor White
Write-Host "    Ctrl+Alt+S   Start / Pause" -ForegroundColor DarkGray
Write-Host "    Ctrl+Alt+Q   Quit" -ForegroundColor DarkGray
Write-Host "    Ctrl+Alt+H   Hide tray icon" -ForegroundColor DarkGray
Write-Host ""
if ($IsWin) {
    Write-Host "  Uninstall:" -ForegroundColor White
    Write-Host "    Remove-Item -Recurse ~\.phantom, ~\.local\bin\phantom.*" -ForegroundColor DarkGray
} else {
    Write-Host "  Uninstall:" -ForegroundColor White
    Write-Host "    rm -rf ~/.phantom ~/.local/bin/phantom" -ForegroundColor DarkGray
}
Write-Host ""
