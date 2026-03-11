"""Abstract base class for all simulators."""

from __future__ import annotations

import abc
import logging
from typing import Any


class BaseSimulator(abc.ABC):
    """All simulators inherit from this and implement execute()."""

    def __init__(self) -> None:
        self.log = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def execute(self, config: Any) -> None:
        """Perform one round of simulated activity."""

    @property
    def name(self) -> str:
        return self.__class__.__name__
