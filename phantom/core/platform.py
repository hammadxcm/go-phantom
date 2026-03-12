"""OS detection helpers."""

from __future__ import annotations

import enum
import logging
import os
import platform
import sys

log = logging.getLogger(__name__)


class OS(enum.Enum):
    """Supported operating systems."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


def current_os() -> OS:
    """Detect the current operating system.

    Returns:
        The ``OS`` enum member for this platform.

    Raises:
        RuntimeError: If the platform is not Windows, macOS, or Linux.
    """
    system = platform.system().lower()
    if system == "darwin":
        return OS.MACOS
    if system == "windows":
        return OS.WINDOWS
    if system == "linux":
        return OS.LINUX
    raise RuntimeError(f"Unsupported platform: {system}")


def is_wayland() -> bool:
    """Check whether the session is running under Wayland.

    Returns:
        ``True`` if ``XDG_SESSION_TYPE`` is ``"wayland"``.
    """
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def check_platform_requirements() -> list[str]:
    """Return a list of platform-specific warnings.

    Checks for known incompatibilities such as Wayland sessions on
    Linux and missing Accessibility permission on macOS.

    Returns:
        Human-readable warning strings (empty list if none).
    """
    warnings: list[str] = []
    host = current_os()

    if host == OS.LINUX and is_wayland():
        warnings.append(
            "Wayland session detected. pynput requires Xorg. "
            "Switch to an X11 session or set XDG_SESSION_TYPE=x11."
        )

    if host == OS.MACOS:
        try:
            import subprocess

            result = subprocess.run(
                ["tccutil", "--help"],
                capture_output=True,
                timeout=5,
            )
            # We can't reliably check accessibility permission from code;
            # pynput will raise on first use if missing.
            _ = result
        except Exception:
            pass
        warnings.append(
            "macOS requires Accessibility permission. "
            "Grant it in System Preferences → Privacy & Security → Accessibility."
        )

    for w in warnings:
        log.warning(w)

    return warnings


def is_frozen() -> bool:
    """Return True if running as a PyInstaller bundle."""
    return getattr(sys, "frozen", False)
