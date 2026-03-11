@echo off
REM Phantom installer for Windows (Command Prompt)
REM Usage: install.bat
REM
REM For PowerShell users, run: .\install.ps1

echo.
echo   +=======================================+
echo   ^|         Phantom Installer v1.0        ^|
echo   ^|   Cross-platform activity simulator   ^|
echo   +=======================================+
echo.

REM ─── Check for PowerShell ─────────────────────────────────────────────────
where pwsh >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo   [INFO]  Found PowerShell Core, launching installer...
    pwsh -ExecutionPolicy Bypass -File "%~dp0install.ps1"
    goto :eof
)

where powershell >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo   [INFO]  Found Windows PowerShell, launching installer...
    powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"
    goto :eof
)

REM ─── Fallback: manual install ──────────────────────────────────────────────
echo   [WARN]  PowerShell not found. Running minimal installer...
echo.

REM Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   [ERROR] Python not found. Install from https://www.python.org/downloads/
    echo          IMPORTANT: Check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PYVER=%%i
echo   [OK]    Found Python %PYVER%

REM Create install directory
set "INSTALL_DIR=%USERPROFILE%\.phantom"
set "VENV_DIR=%INSTALL_DIR%\.venv"
set "BIN_DIR=%USERPROFILE%\.local\bin"

if not exist "%INSTALL_DIR%\phantom" (
    mkdir "%INSTALL_DIR%" 2>nul
    xcopy /E /I /Q "%~dp0phantom" "%INSTALL_DIR%\phantom"
    copy /Y "%~dp0pyproject.toml" "%INSTALL_DIR%\" >nul
    if exist "%~dp0requirements.txt" copy /Y "%~dp0requirements.txt" "%INSTALL_DIR%\" >nul
    echo   [OK]    Copied project files
) else (
    echo   [INFO]  Existing installation found
)

REM Create venv
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
    echo   [OK]    Created virtual environment
) else (
    echo   [INFO]  Virtual environment exists
)

REM Install
call "%VENV_DIR%\Scripts\activate.bat"
pip install --quiet --upgrade pip 2>nul
pip install --quiet -e "%INSTALL_DIR%"
echo   [OK]    Dependencies installed

REM Create launcher
mkdir "%BIN_DIR%" 2>nul
(
    echo @echo off
    echo call "%VENV_DIR%\Scripts\activate.bat"
    echo python -m phantom %%*
) > "%BIN_DIR%\phantom.cmd"
echo   [OK]    Created %BIN_DIR%\phantom.cmd

REM PATH check
echo %PATH% | find /I "%BIN_DIR%" >nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   [WARN]  %BIN_DIR% is not in your PATH.
    echo.
    echo   Add it with:
    echo     setx PATH "%BIN_DIR%;%%PATH%%"
    echo.
    echo   Or add it manually via:
    echo     System Properties ^> Environment Variables ^> PATH
)

echo.
echo   ! Windows Defender may flag Phantom (it simulates input).
echo     Add an exclusion: Windows Security ^> Exclusions ^> Add folder: %INSTALL_DIR%
echo.
echo   Phantom installed successfully!
echo.
echo   Quick start:
echo     phantom                    Run with defaults
echo     phantom -v                 Run with debug logging
echo     phantom -c config.json     Custom config
echo.
echo   Hotkeys:
echo     Ctrl+Alt+S   Start / Pause
echo     Ctrl+Alt+Q   Quit
echo     Ctrl+Alt+H   Hide tray icon
echo.
echo   Uninstall:
echo     rmdir /s /q "%INSTALL_DIR%" "%BIN_DIR%\phantom.cmd"
echo.
pause
