"""Cross-platform active window detection.

This module provides a unified interface for detecting the currently
focused (foreground) window across macOS, Windows, and Linux (X11).
Results are cached with a short TTL to minimise expensive platform
calls during high-frequency simulator ticks.
"""

from __future__ import annotations

import logging
import subprocess
import threading
import time
from dataclasses import dataclass

from phantom.core.platform import OS, current_os, is_wayland

log = logging.getLogger(__name__)

_CACHE_TTL = 0.5
_lock = threading.Lock()
_cache: tuple[float, WindowInfo | None] = (0.0, None)


@dataclass(frozen=True)
class WindowInfo:
    """Immutable snapshot of the currently focused window.

    Attributes:
        app_name: The name of the application that owns the window.
        window_title: The title text of the window.
    """

    app_name: str
    window_title: str


def get_active_window() -> WindowInfo | None:
    """Return the foreground window info with a short TTL cache.

    Uses a module-level lock to ensure thread-safe cache access.
    Results are cached for ``_CACHE_TTL`` seconds to avoid expensive
    platform calls on every simulator tick.

    Returns:
        WindowInfo for the active window, or None if detection fails.
    """
    global _cache
    with _lock:
        now = time.monotonic()
        if now - _cache[0] < _CACHE_TTL:
            return _cache[1]
        result = _detect()
        _cache = (now, result)
        return result


def _detect() -> WindowInfo | None:
    """Dispatch to the platform-specific detection implementation.

    Returns:
        WindowInfo for the active window, or None if detection fails
        or the current platform is unsupported.
    """
    os = current_os()
    try:
        if os == OS.MACOS:
            return _detect_macos()
        if os == OS.WINDOWS:
            return _detect_windows()
        if os == OS.LINUX:
            return _detect_linux()
    except Exception:
        log.debug("Active window detection failed", exc_info=True)
    return None


def _detect_macos() -> WindowInfo | None:
    """Detect the active window on macOS using AppleScript.

    Returns:
        WindowInfo with the frontmost application name and window
        title, or None if the AppleScript invocation fails.
    """
    script = (
        'tell application "System Events"\n'
        "  set frontApp to first application process whose frontmost is true\n"
        "  set appName to name of frontApp\n"
        "  set winTitle to \"\"\n"
        "  try\n"
        "    set winTitle to name of front window of frontApp\n"
        "  end try\n"
        '  return appName & "||" & winTitle\n'
        "end tell"
    )
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=2,
    )
    if result.returncode != 0:
        return None
    parts = result.stdout.strip().split("||", 1)
    if len(parts) != 2:
        return None
    return WindowInfo(app_name=parts[0].strip(), window_title=parts[1].strip())


def _detect_windows() -> WindowInfo | None:
    """Detect the active window on Windows using the Win32 API.

    Returns:
        WindowInfo with the process name and window title, or None
        if no foreground window is found.
    """
    import ctypes

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    # Get window title
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value

    # Get process name
    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    handle = kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid.value
    )
    if not handle:
        return WindowInfo(app_name="", window_title=title)

    try:
        psapi = ctypes.windll.psapi  # type: ignore[attr-defined]
        name_buf = ctypes.create_unicode_buffer(260)
        psapi.GetModuleBaseNameW(handle, None, name_buf, 260)
        app_name = name_buf.value
    finally:
        kernel32.CloseHandle(handle)

    return WindowInfo(app_name=app_name, window_title=title)


def _detect_linux() -> WindowInfo | None:
    """Detect the active window on Linux (X11) using xdotool/xprop.

    Wayland is not supported and will return None immediately.

    Returns:
        WindowInfo with the WM_CLASS and window title, or None if
        detection fails or the session is running Wayland.
    """
    if is_wayland():
        log.debug("Wayland detected; active window detection not supported")
        return None

    # Get active window ID
    wid_result = subprocess.run(
        ["xdotool", "getactivewindow"],
        capture_output=True,
        text=True,
        timeout=2,
    )
    if wid_result.returncode != 0:
        return None
    wid = wid_result.stdout.strip()

    # Get window title
    title_result = subprocess.run(
        ["xdotool", "getactivewindow", "getwindowname"],
        capture_output=True,
        text=True,
        timeout=2,
    )
    title = title_result.stdout.strip() if title_result.returncode == 0 else ""

    # Get WM_CLASS for app name
    prop_result = subprocess.run(
        ["xprop", "-id", wid, "WM_CLASS"],
        capture_output=True,
        text=True,
        timeout=2,
    )
    app_name = ""
    if prop_result.returncode == 0:
        # WM_CLASS output: WM_CLASS(STRING) = "instance", "class"
        line = prop_result.stdout.strip()
        if '"' in line:
            parts = line.split('"')
            # Use the class name (second quoted string)
            app_name = parts[3] if len(parts) >= 4 else parts[1]

    return WindowInfo(app_name=app_name, window_title=title)
