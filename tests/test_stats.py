"""Tests for phantom.core.stats."""

from __future__ import annotations

import threading
import time

from phantom.core.stats import Stats


class TestStatsBasic:
    def test_initial_state(self):
        stats = Stats()
        snap = stats.snapshot()
        assert snap["total_actions"] == 0
        assert snap["actions_by_simulator"] == {}
        assert snap["last_action_name"] is None
        assert snap["last_action_time"] is None
        assert snap["pauses"] == 0
        assert snap["active"] is False

    def test_record_action(self):
        stats = Stats()
        stats.record_action("mouse")
        snap = stats.snapshot()
        assert snap["total_actions"] == 1
        assert snap["actions_by_simulator"] == {"mouse": 1}
        assert snap["last_action_name"] == "mouse"
        assert snap["last_action_time"] is not None

    def test_record_multiple_actions(self):
        stats = Stats()
        stats.record_action("mouse")
        stats.record_action("mouse")
        stats.record_action("keyboard")
        snap = stats.snapshot()
        assert snap["total_actions"] == 3
        assert snap["actions_by_simulator"] == {"mouse": 2, "keyboard": 1}
        assert snap["last_action_name"] == "keyboard"

    def test_uptime(self):
        stats = Stats()
        time.sleep(0.05)
        assert stats.uptime() >= 0.04

    def test_uptime_in_snapshot(self):
        stats = Stats()
        time.sleep(0.05)
        snap = stats.snapshot()
        assert snap["uptime"] >= 0.04

    def test_mark_active(self):
        stats = Stats()
        stats.mark_active(True)
        snap = stats.snapshot()
        assert snap["active"] is True
        assert snap["pauses"] == 0

    def test_mark_inactive_counts_pause(self):
        stats = Stats()
        stats.mark_active(True)
        stats.mark_active(False)
        snap = stats.snapshot()
        assert snap["active"] is False
        assert snap["pauses"] == 1

    def test_mark_inactive_without_active_no_pause(self):
        stats = Stats()
        stats.mark_active(False)
        snap = stats.snapshot()
        assert snap["pauses"] == 0

    def test_multiple_pauses(self):
        stats = Stats()
        stats.mark_active(True)
        stats.mark_active(False)
        stats.mark_active(True)
        stats.mark_active(False)
        snap = stats.snapshot()
        assert snap["pauses"] == 2

    def test_snapshot_is_frozen_copy(self):
        stats = Stats()
        stats.record_action("mouse")
        snap = stats.snapshot()
        stats.record_action("keyboard")
        assert snap["total_actions"] == 1  # snapshot unaffected

    def test_snapshot_actions_dict_is_copy(self):
        stats = Stats()
        stats.record_action("mouse")
        snap = stats.snapshot()
        snap["actions_by_simulator"]["scroll"] = 99
        snap2 = stats.snapshot()
        assert "scroll" not in snap2["actions_by_simulator"]


class TestStatsThreadSafety:
    def test_concurrent_record(self):
        stats = Stats()
        errors = []

        def worker(name, count):
            try:
                for _ in range(count):
                    stats.record_action(name)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=("mouse", 100)),
            threading.Thread(target=worker, args=("keyboard", 100)),
            threading.Thread(target=worker, args=("scroll", 100)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        snap = stats.snapshot()
        assert snap["total_actions"] == 300
        assert snap["actions_by_simulator"]["mouse"] == 100
        assert snap["actions_by_simulator"]["keyboard"] == 100
        assert snap["actions_by_simulator"]["scroll"] == 100

    def test_concurrent_mark_active(self):
        stats = Stats()
        errors = []

        def toggler(count):
            try:
                for i in range(count):
                    stats.mark_active(i % 2 == 0)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=toggler, args=(50,)) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        # Just verify it didn't crash; exact pause count depends on interleaving

    def test_concurrent_snapshot(self):
        stats = Stats()
        errors = []

        def recorder():
            for _ in range(50):
                stats.record_action("mouse")

        def snapshotter():
            try:
                for _ in range(50):
                    snap = stats.snapshot()
                    assert isinstance(snap, dict)
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=recorder)
        t2 = threading.Thread(target=snapshotter)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert not errors
