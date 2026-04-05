"""Abstract base class for all activity simulators.

Every simulator must subclass :class:`BaseSimulator` and implement the
:meth:`execute` method. The scheduler calls ``execute`` once per action
cycle, passing the simulator's typed configuration dataclass.
"""

from __future__ import annotations

import abc
import logging
from typing import Any


class BaseSimulator(abc.ABC):
    """Base class that all simulators must inherit from.

    Subclasses must implement :meth:`execute` to perform one round of
    simulated user activity. Each instance gets a dedicated logger
    namespaced under ``phantom.simulators.<module>``.
    """

    def __init__(self) -> None:
        """Initialize the simulator with a module-scoped logger."""
        self.log = logging.getLogger(
            f"phantom.simulators.{type(self).__module__.rsplit('.', 1)[-1]}"
        )

    @abc.abstractmethod
    def execute(self, config: Any) -> str:
        """Perform one round of simulated activity.

        Args:
            config: Typed configuration dataclass for this simulator.

        Returns:
            A human-readable detail string describing what happened.
        """

    @property
    def name(self) -> str:
        """Return the class name of this simulator."""
        return self.__class__.__name__
