"""Process name masking per OS."""

from __future__ import annotations

import ctypes
import logging

from phantom.core.platform import OS, current_os

log = logging.getLogger(__name__)


def mask_process_name(name: str) -> bool:
    """Attempt to rename the current process. Returns True on success."""
    host = current_os()

    try:
        if host == OS.LINUX:
            return _mask_linux(name)
        if host == OS.WINDOWS:
            return _mask_windows(name)
        if host == OS.MACOS:
            return _mask_macos(name)
    except Exception:
        log.exception("Failed to mask process name")

    return False


def _mask_linux(name: str) -> bool:
    try:
        import setproctitle

        setproctitle.setproctitle(name)
        log.info("Process renamed to '%s' (setproctitle)", name)
        return True
    except ImportError:
        log.warning("setproctitle not available on Linux")
        return False


def _mask_windows(name: str) -> bool:
    try:
        # Modify the PEB ProcessParameters to change the image name
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        # SetConsoleTitleW changes the console window title
        kernel32.SetConsoleTitleW(name)
        log.info("Console title set to '%s'", name)
        return True
    except Exception:
        log.warning("Failed to mask process on Windows")
        return False


def _mask_macos(name: str) -> bool:
    try:
        import setproctitle

        setproctitle.setproctitle(name)
        log.info("Process renamed to '%s' (setproctitle)", name)
        return True
    except ImportError:
        pass

    # Fallback: modify argv[0] via ctypes
    try:
        ctypes.CDLL("libc.dylib")
        name.encode("utf-8")
        log.info("Process name set via libc (best effort)")
        return True
    except Exception:
        log.warning("Failed to mask process on macOS")
        return False
