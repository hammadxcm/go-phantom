"""Central action loop with weighted random selection and gaussian timing."""

from __future__ import annotations

import logging
import threading

from phantom.config.schema import PhantomConfig
from phantom.core.randomization import Randomizer
from phantom.core.stats import Stats
from phantom.simulators.base import BaseSimulator
from phantom.stealth.anti_detection import AntiDetection

log = logging.getLogger(__name__)


class Scheduler:
    """Runs the main simulation loop in a daemon thread."""

    def __init__(
        self,
        config: PhantomConfig,
        simulators: dict[str, BaseSimulator],
        config_lock: threading.Lock,
        stats: Stats | None = None,
    ) -> None:
        self._config = config
        self._simulators = simulators
        self._config_lock = config_lock
        self._running = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._anti_detection = AntiDetection()
        self._stats = stats

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._running.set()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="phantom-scheduler")
        self._thread.start()
        if self._stats:
            self._stats.mark_active(True)
        log.info("Scheduler started")

    def stop(self) -> None:
        self._running.clear()
        self._stop.set()
        if self._stats:
            self._stats.mark_active(False)
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        log.info("Scheduler stopped")

    def toggle(self) -> bool:
        """Toggle running state. Returns new state."""
        if self._running.is_set():
            self.stop()
            return False
        self.start()
        return True

    def shutdown(self) -> None:
        self.stop()

    def _loop(self) -> None:
        log.info("Simulation loop started")
        while not self._stop.is_set():
            if not self._running.is_set():
                self._stop.wait(timeout=0.5)
                continue

            with self._config_lock:
                weights = self._config.simulator_weights()
                timing = self._config.timing

            if not weights:
                log.warning("No simulators enabled, waiting...")
                self._stop.wait(timeout=2.0)
                continue

            # Check for idle period
            if Randomizer.should_idle():
                idle_time = Randomizer.idle_duration()
                log.debug("Idle period: %.1fs", idle_time)
                self._stop.wait(timeout=idle_time)
                if self._stop.is_set():
                    break
                continue

            # Select and execute a simulator
            options = list(weights.items())
            chosen = Randomizer.weighted_choice(options)

            # Anti-detection: avoid repetitive patterns
            if self._anti_detection.would_be_repetitive(chosen):
                remaining = [(n, w) for n, w in options if n != chosen]
                if remaining:
                    chosen = Randomizer.weighted_choice(remaining)

            sim = self._simulators.get(chosen)
            if sim is None:
                continue

            try:
                sim_config = self._get_sim_config(chosen)
                sim.execute(sim_config)
                self._anti_detection.record(chosen)
                if self._stats:
                    self._stats.record_action(chosen)
            except Exception:
                log.exception("Simulator %s failed", chosen)

            # Wait before next action
            interval = Randomizer.action_interval(
                mean=timing.interval_mean,
                stddev=timing.interval_stddev,
                minimum=timing.interval_min,
            )
            self._stop.wait(timeout=interval)

        log.info("Simulation loop exited")

    def _get_sim_config(self, name: str):
        """Get the config section for a named simulator."""
        with self._config_lock:
            return getattr(self._config, name)
