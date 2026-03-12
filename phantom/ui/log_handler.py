"""Bounded deque log handler for TUI dashboard display.

This module provides a thread-safe logging handler that stores formatted
log records in a bounded deque, suitable for rendering in a terminal-based
dashboard.  Entries are evicted by both count and age so the display always
reflects recent activity without unbounded memory growth.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque


class DequeHandler(logging.Handler):
    """Thread-safe logging handler backed by a bounded deque.

    Captures formatted log records into a fixed-size deque for consumption
    by a TUI dashboard.  Entries are bounded both by count (``maxlen``) and
    by wall-clock age (``max_age_secs``).  Stale entries older than
    ``max_age_secs`` are pruned automatically on each read.

    Attributes:
        maxlen: Maximum number of log entries retained.
    """

    def __init__(self, maxlen: int = 200, max_age_secs: float = 300.0) -> None:
        """Initialise the handler with size and age limits.

        Args:
            maxlen: Maximum number of log entries to keep in the deque.
                Older entries are discarded once this limit is reached.
            max_age_secs: Maximum age in seconds for a log entry.  Entries
                older than this are pruned on the next read access.
        """
        super().__init__()
        self._records: deque[str] = deque(maxlen=maxlen)
        self._structured: deque[tuple[str, str, int, float]] = deque(maxlen=maxlen)
        self._maxlen = maxlen
        self._max_age = max_age_secs
        self._lock = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        """Format and store a log record in the deque.

        The record is formatted via the handler's formatter, timestamped
        with :func:`time.monotonic`, and appended to both the plain-text
        and structured deques.

        Args:
            record: The log record emitted by the logging framework.
        """
        with self._lock:
            try:
                msg = self.format(record)
                now = time.monotonic()
                self._records.append(msg)
                self._structured.append((msg, record.name, record.levelno, now))
            except Exception:
                self.handleError(record)

    def _prune_stale(self) -> None:
        """Remove entries older than ``max_age_secs``.

        Iterates from the oldest entry forward, popping items whose
        monotonic timestamp is before the cutoff.  Must be called while
        ``self._lock`` is held.
        """
        cutoff = time.monotonic() - self._max_age
        while self._structured and self._structured[0][3] < cutoff:
            self._structured.popleft()
            if self._records:
                self._records.popleft()

    @property
    def lines(self) -> list[str]:
        """Return current log lines as a plain-text list.

        Stale entries are pruned before the snapshot is taken.

        Returns:
            A list of formatted log-line strings, oldest first.
        """
        with self._lock:
            self._prune_stale()
            return list(self._records)

    @property
    def lines_styled(self) -> list[tuple[str, str, int]]:
        """Return structured log entries for styled rendering.

        Each tuple contains the formatted message, the originating logger
        name, and the numeric log level.  Stale entries are pruned before
        the snapshot is taken.

        Returns:
            A list of ``(formatted_msg, logger_name, level)`` tuples,
            oldest first.
        """
        with self._lock:
            self._prune_stale()
            return [(msg, name, level) for msg, name, level, _ts in self._structured]

    @property
    def maxlen(self) -> int:
        """The maximum number of log entries the handler retains.

        Returns:
            The ``maxlen`` value provided at construction time.
        """
        return self._maxlen
