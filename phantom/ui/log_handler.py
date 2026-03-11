"""Bounded deque log handler for TUI dashboard display."""

from __future__ import annotations

import logging
from collections import deque


class DequeHandler(logging.Handler):
    """Captures formatted log records into a bounded deque for TUI display."""

    def __init__(self, maxlen: int = 200) -> None:
        super().__init__()
        self._records: deque[str] = deque(maxlen=maxlen)
        self._maxlen = maxlen

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._records.append(msg)
        except Exception:
            self.handleError(record)

    @property
    def lines(self) -> list[str]:
        """Return current log lines as a list."""
        return list(self._records)

    @property
    def maxlen(self) -> int:
        return self._maxlen
