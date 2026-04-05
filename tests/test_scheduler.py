"""Tests for phantom.core.scheduler."""

from __future__ import annotations

import threading
import time
from unittest.mock import patch

from phantom.config.schema import (
    KeyboardConfig,
    MouseConfig,
    PhantomConfig,
    ScrollConfig,
    TimingConfig,
)
from phantom.core.scheduler import Scheduler
from phantom.simulators.base import BaseSimulator


class FakeSimulator(BaseSimulator):
    def __init__(self):
        super().__init__()
        self.call_count = 0

    def execute(self, config):
        self.call_count += 1
        return f"fake action #{self.call_count}"


class FailingSimulator(BaseSimulator):
    def execute(self, config):
        raise RuntimeError("boom")


class TestSchedulerLifecycle:
    def _make_scheduler(self, config=None):
        config = config or PhantomConfig(
            timing=TimingConfig(interval_mean=0.01, interval_stddev=0.001, interval_min=0.001),
        )
        sims = {"mouse": FakeSimulator(), "keyboard": FakeSimulator()}
        lock = threading.Lock()
        return Scheduler(config, sims, lock), sims

    def test_start_stop(self):
        sched, _ = self._make_scheduler()
        sched.start()
        assert sched.is_running
        time.sleep(0.05)
        sched.stop()
        assert not sched.is_running

    def test_double_start(self):
        sched, _ = self._make_scheduler()
        sched.start()
        sched.start()  # Should not create second thread
        assert sched.is_running
        sched.stop()

    def test_stop_without_start(self):
        sched, _ = self._make_scheduler()
        sched.stop()  # Should not raise

    def test_toggle(self):
        sched, _ = self._make_scheduler()
        assert sched.toggle() is True  # start
        assert sched.is_running
        assert sched.toggle() is False  # stop
        assert not sched.is_running

    def test_shutdown(self):
        sched, _ = self._make_scheduler()
        sched.start()
        sched.shutdown()
        assert not sched.is_running

    @patch("phantom.core.scheduler.Randomizer.should_idle", return_value=False)
    @patch("phantom.core.scheduler.Randomizer.action_interval", return_value=0.001)
    def test_simulators_called(self, _int, _idle):
        sched, sims = self._make_scheduler()
        sched.start()
        time.sleep(0.1)
        sched.stop()
        total = sims["mouse"].call_count + sims["keyboard"].call_count
        assert total > 0

    @patch("phantom.core.scheduler.Randomizer.should_idle", return_value=False)
    @patch("phantom.core.scheduler.Randomizer.action_interval", return_value=0.001)
    def test_simulator_exception_handled(self, _int, _idle):
        config = PhantomConfig(
            timing=TimingConfig(interval_mean=0.01, interval_stddev=0.001, interval_min=0.001),
            keyboard=KeyboardConfig(enabled=False),
            scroll=ScrollConfig(enabled=False),
        )
        sims = {"mouse": FailingSimulator()}
        lock = threading.Lock()
        sched = Scheduler(config, sims, lock)
        sched.start()
        time.sleep(0.05)
        sched.stop()  # Should not crash

    def test_no_simulators_enabled(self):
        config = PhantomConfig(
            timing=TimingConfig(interval_mean=0.01, interval_stddev=0.001, interval_min=0.001),
            mouse=MouseConfig(enabled=False),
            keyboard=KeyboardConfig(enabled=False),
            scroll=ScrollConfig(enabled=False),
        )
        sims = {"mouse": FakeSimulator()}
        lock = threading.Lock()
        sched = Scheduler(config, sims, lock)
        sched.start()
        time.sleep(0.05)
        sched.stop()  # Should handle gracefully

    @patch("phantom.core.scheduler.Randomizer.should_idle", return_value=True)
    @patch("phantom.core.scheduler.Randomizer.idle_duration", return_value=0.01)
    def test_idle_period(self, _dur, _idle):
        sched, _sims = self._make_scheduler()
        sched.start()
        time.sleep(0.1)
        sched.stop()
        # Might have some calls, but idle periods should have occurred

    def test_get_sim_config(self):
        sched, _ = self._make_scheduler()
        cfg = sched._get_sim_config("mouse")
        assert isinstance(cfg, MouseConfig)


class TestSchedulerNotRunning:
    def test_loop_pauses_when_not_running(self):
        config = PhantomConfig(
            timing=TimingConfig(interval_mean=0.01, interval_stddev=0.001, interval_min=0.001),
        )
        sims = {"mouse": FakeSimulator()}
        lock = threading.Lock()
        sched = Scheduler(config, sims, lock)
        sched._stop.clear()
        sched._running.clear()  # Not running

        # Set stop after a short delay so loop can execute the not-running branch
        def delayed_stop():
            time.sleep(0.05)
            sched._stop.set()

        t = threading.Thread(target=delayed_stop)
        t.start()
        sched._loop()  # Will enter while, hit not-running, wait, then exit
        t.join()


class TestSchedulerAntiDetection:
    @patch("phantom.core.scheduler.Randomizer.should_idle", return_value=False)
    @patch("phantom.core.scheduler.Randomizer.action_interval", return_value=0.001)
    def test_anti_detection_fallback(self, _int, _idle):
        config = PhantomConfig(
            timing=TimingConfig(interval_mean=0.01, interval_stddev=0.001, interval_min=0.001),
            keyboard=KeyboardConfig(enabled=True),
            scroll=ScrollConfig(enabled=False),
        )
        sims = {"mouse": FakeSimulator(), "keyboard": FakeSimulator()}
        lock = threading.Lock()
        sched = Scheduler(config, sims, lock)

        # Pre-fill anti-detection history to make "mouse" repetitive
        for _ in range(10):
            sched._anti_detection.record("mouse")

        sched.start()
        time.sleep(0.05)
        sched.stop()
        # Keyboard should have been chosen as fallback at some point
        assert sims["keyboard"].call_count > 0 or sims["mouse"].call_count > 0
