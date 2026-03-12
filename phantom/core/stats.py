"""Thread-safe metrics collector for TUI dashboard."""

from __future__ import annotations

import threading
import time


class Stats:
    """Collects runtime metrics in a thread-safe manner.

    All public methods are safe to call from any thread. Use
    :meth:`snapshot` to obtain a consistent copy of all counters.
    """

    def __init__(self) -> None:
        """Initialize counters and record the start time."""
        self._lock = threading.Lock()
        self._start_time = time.monotonic()
        self._total_actions = 0
        self._actions_by_simulator: dict[str, int] = {}
        self._last_action_name: str | None = None
        self._last_action_time: float | None = None
        self._pauses = 0
        self._active = False

    def record_action(self, name: str) -> None:
        """Record that a simulator action was executed.

        Args:
            name: Simulator name (e.g. ``"mouse"``, ``"keyboard"``).
        """
        with self._lock:
            self._total_actions += 1
            self._actions_by_simulator[name] = self._actions_by_simulator.get(name, 0) + 1
            self._last_action_name = name
            self._last_action_time = time.monotonic()

    def uptime(self) -> float:
        """Seconds since stats were initialized.

        Returns:
            Elapsed wall-clock seconds as a float.
        """
        return time.monotonic() - self._start_time

    def mark_active(self, active: bool) -> None:
        """Track pause/resume transitions.

        Args:
            active: ``True`` when the scheduler starts, ``False`` when it stops.
        """
        with self._lock:
            if not active and self._active:
                self._pauses += 1
            self._active = active

    def snapshot(self) -> dict:
        """Return a frozen copy of all metrics.

        Returns:
            Dict with keys: ``uptime`` (float), ``total_actions`` (int),
            ``actions_by_simulator`` (dict), ``last_action_name`` (str | None),
            ``last_action_time`` (float | None), ``pauses`` (int),
            ``active`` (bool).
        """
        with self._lock:
            return {
                "uptime": time.monotonic() - self._start_time,
                "total_actions": self._total_actions,
                "actions_by_simulator": dict(self._actions_by_simulator),
                "last_action_name": self._last_action_name,
                "last_action_time": self._last_action_time,
                "pauses": self._pauses,
                "active": self._active,
            }
