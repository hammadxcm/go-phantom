"""Pattern variation and history tracking to avoid repetitive sequences."""

from __future__ import annotations

import collections
import logging

log = logging.getLogger(__name__)

HISTORY_SIZE = 100
REPETITION_THRESHOLD = 4  # Max consecutive same-action count


class AntiDetection:
    """Tracks action history and flags repetitive patterns.

    Maintains a bounded deque of recent action names and detects
    consecutive or alternating sequences that could appear bot-like.
    """

    def __init__(self) -> None:
        """Initialize with an empty history buffer."""
        self._history: collections.deque[str] = collections.deque(maxlen=HISTORY_SIZE)

    def record(self, action: str) -> None:
        """Append an action name to the history buffer.

        Args:
            action: Simulator name that was just executed.
        """
        self._history.append(action)

    def would_be_repetitive(self, action: str) -> bool:
        """Check whether executing *action* would create a repetitive pattern.

        Args:
            action: Simulator name being considered.

        Returns:
            ``True`` if the action would result in a consecutive run or
            alternating A-B pattern that exceeds the threshold.
        """
        if len(self._history) < REPETITION_THRESHOLD:
            return False

        recent = list(self._history)[-REPETITION_THRESHOLD:]
        if all(a == action for a in recent):
            log.debug("Blocked repetitive action: %s", action)
            return True

        # Detect alternating A-B-A-B pattern
        if len(self._history) >= 6:
            last6 = list(self._history)[-6:]
            if last6[0] == last6[2] == last6[4] == action and last6[1] == last6[3] == last6[5]:
                log.debug("Blocked alternating pattern: %s", action)
                return True

        return False

    @property
    def history(self) -> list:
        """Return a snapshot of the action history.

        Returns:
            List of action name strings, oldest first.
        """
        return list(self._history)
