"""Tests for phantom.stealth.anti_detection."""

from __future__ import annotations

from phantom.stealth.anti_detection import HISTORY_SIZE, REPETITION_THRESHOLD, AntiDetection


class TestAntiDetection:
    def test_empty_history(self):
        ad = AntiDetection()
        assert ad.history == []
        assert ad.would_be_repetitive("mouse") is False

    def test_record_adds_to_history(self):
        ad = AntiDetection()
        ad.record("mouse")
        ad.record("keyboard")
        assert ad.history == ["mouse", "keyboard"]

    def test_history_max_size(self):
        ad = AntiDetection()
        for i in range(HISTORY_SIZE + 10):
            ad.record(f"action_{i}")
        assert len(ad.history) == HISTORY_SIZE

    def test_not_repetitive_below_threshold(self):
        ad = AntiDetection()
        for _ in range(REPETITION_THRESHOLD - 1):
            ad.record("mouse")
        assert ad.would_be_repetitive("mouse") is False

    def test_repetitive_at_threshold(self):
        ad = AntiDetection()
        for _ in range(REPETITION_THRESHOLD):
            ad.record("mouse")
        assert ad.would_be_repetitive("mouse") is True

    def test_not_repetitive_mixed(self):
        ad = AntiDetection()
        ad.record("mouse")
        ad.record("keyboard")
        ad.record("mouse")
        ad.record("keyboard")
        assert ad.would_be_repetitive("scroll") is False

    def test_alternating_pattern_detected(self):
        ad = AntiDetection()
        # Create A-B-A-B-A-B pattern
        for _ in range(3):
            ad.record("mouse")
            ad.record("keyboard")
        # Next "mouse" would continue the alternating pattern
        assert ad.would_be_repetitive("mouse") is True

    def test_alternating_pattern_not_triggered_with_variety(self):
        ad = AntiDetection()
        ad.record("mouse")
        ad.record("keyboard")
        ad.record("scroll")
        ad.record("mouse")
        ad.record("keyboard")
        ad.record("scroll")
        assert ad.would_be_repetitive("mouse") is False

    def test_different_action_breaks_repetition(self):
        ad = AntiDetection()
        for _ in range(REPETITION_THRESHOLD):
            ad.record("mouse")
        # "keyboard" should not be flagged as repetitive
        assert ad.would_be_repetitive("keyboard") is False

    def test_short_history_no_alternating_check(self):
        ad = AntiDetection()
        ad.record("a")
        ad.record("b")
        ad.record("a")
        ad.record("b")
        # Only 4 entries, alternating check needs 6
        assert ad.would_be_repetitive("a") is False
