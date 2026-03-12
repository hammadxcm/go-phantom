"""Process name masking per OS."""

from __future__ import annotations

import ctypes
import logging

from phantom.core.platform import OS, current_os

log = logging.getLogger(__name__)


def mask_process_name(name: str) -> bool:
    """Attempt to rename the current process.

    Delegates to a platform-specific helper based on the detected OS.

    Args:
        name: Desired process name.

    Returns:
        True if the process was successfully renamed.
    """
    host = current_os()

    try:
        if host == OS.LINUX:
            return _mask_linux(name)
        if host == OS.WINDOWS:
            return _mask_windows(name)
        if host == OS.MACOS:
            return _mask_macos(name)
    except (OSError, ImportError, AttributeError):
        log.exception("Failed to mask process name")

    return False


def _mask_linux(name: str) -> bool:
    """Rename the current process on Linux using ``setproctitle``.

    Args:
        name: Desired process name.

    Returns:
        True if the process was successfully renamed.
    """
    try:
        import setproctitle

        setproctitle.setproctitle(name)
        log.info("Process renamed to '%s' (setproctitle)", name)
        return True
    except ImportError:
        log.warning("setproctitle not available on Linux")
        return False


def _mask_windows(name: str) -> bool:
    """Rename the console window title on Windows via ``kernel32``.

    Args:
        name: Desired process/console title.

    Returns:
        True if the console title was successfully changed.
    """
    try:
        # Modify the PEB ProcessParameters to change the image name
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        # SetConsoleTitleW changes the console window title
        kernel32.SetConsoleTitleW(name)
        log.info("Console title set to '%s'", name)
        return True
    except (OSError, AttributeError):
        log.warning("Failed to mask process on Windows")
        return False


def _mask_macos(name: str) -> bool:
    """Rename the current process on macOS.

    Requires the ``setproctitle`` package. The previous ctypes/libc fallback
    loaded the library but never actually called any renaming function, so it
    has been removed.

    Args:
        name: Desired process name.

    Returns:
        True if the process was successfully renamed.
    """
    try:
        import setproctitle

        setproctitle.setproctitle(name)
        log.info("Process renamed to '%s' (setproctitle)", name)
        return True
    except ImportError:
        log.warning(
            "setproctitle not available; process masking requires "
            "'pip install setproctitle' on macOS"
        )
        return False
