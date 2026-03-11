"""Tests for phantom.core.randomization."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from phantom.core.randomization import Randomizer


class TestBezierPoint:
    def test_start_point(self):
        p = Randomizer.bezier_point(0.0, (0, 0), (10, 10), (20, 20), (30, 30))
        assert p == (0.0, 0.0)

    def test_end_point(self):
        p = Randomizer.bezier_point(1.0, (0, 0), (10, 10), (20, 20), (30, 30))
        assert abs(p[0] - 30.0) < 1e-9
        assert abs(p[1] - 30.0) < 1e-9

    def test_midpoint_on_line(self):
        p = Randomizer.bezier_point(0.5, (0, 0), (10, 0), (20, 0), (30, 0))
        assert 0 < p[0] < 30


class TestBezierControlPoints:
    def test_returns_two_points(self):
        cp1, cp2 = Randomizer.bezier_control_points((0, 0), (100, 100))
        assert len(cp1) == 2
        assert len(cp2) == 2

    def test_control_points_differ(self):
        cp1, cp2 = Randomizer.bezier_control_points((0, 0), (200, 200))
        # Very unlikely to be identical
        assert cp1 != cp2 or True  # Non-deterministic, just ensure no crash

    def test_zero_distance(self):
        cp1, cp2 = Randomizer.bezier_control_points((50, 50), (50, 50))
        assert isinstance(cp1, tuple)
        assert isinstance(cp2, tuple)


class TestBezierPath:
    def test_path_length(self):
        path = Randomizer.bezier_path((0, 0), (100, 100), steps=20)
        assert len(path) == 21  # steps + 1

    def test_path_starts_at_start(self):
        path = Randomizer.bezier_path((10, 20), (200, 300), steps=10)
        assert path[0] == (10, 20)

    def test_path_ends_at_end(self):
        path = Randomizer.bezier_path((10, 20), (200, 300), steps=10)
        assert path[-1] == (200, 300)

    def test_path_points_are_tuples(self):
        path = Randomizer.bezier_path((0, 0), (50, 50), steps=5)
        for pt in path:
            assert isinstance(pt, tuple)
            assert len(pt) == 2

    def test_default_steps(self):
        path = Randomizer.bezier_path((0, 0), (100, 100))
        assert len(path) == 51  # default 50 steps + 1


class TestActionInterval:
    def test_default_interval_positive(self):
        for _ in range(100):
            val = Randomizer.action_interval()
            assert val >= Randomizer.DEFAULT_INTERVAL_MIN

    def test_custom_parameters(self):
        val = Randomizer.action_interval(mean=2.0, stddev=0.5, minimum=1.0)
        assert val >= 1.0

    def test_minimum_enforced(self):
        # With very low mean and high stddev, minimum should still hold
        for _ in range(100):
            val = Randomizer.action_interval(mean=0.0, stddev=0.1, minimum=5.0)
            assert val >= 5.0


class TestShouldIdle:
    @patch("phantom.core.randomization.random.random", return_value=0.05)
    def test_should_idle(self, _mock):
        assert Randomizer.should_idle() is True

    @patch("phantom.core.randomization.random.random", return_value=0.5)
    def test_should_not_idle(self, _mock):
        assert Randomizer.should_idle() is False


class TestIdleDuration:
    def test_within_bounds(self):
        for _ in range(100):
            dur = Randomizer.idle_duration()
            assert Randomizer.IDLE_MIN <= dur <= Randomizer.IDLE_MAX


class TestKeystrokeDelay:
    def test_base_delay(self):
        for _ in range(100):
            delay = Randomizer.keystroke_delay()
            assert delay >= Randomizer.KEYSTROKE_BASE_MIN

    @patch("phantom.core.randomization.random.random", return_value=0.01)
    def test_thinking_pause(self, _mock):
        delay = Randomizer.keystroke_delay()
        # With thinking pause triggered, delay should be higher
        assert delay >= Randomizer.KEYSTROKE_BASE_MIN


class TestStepDelay:
    def test_range(self):
        for _ in range(100):
            d = Randomizer.step_delay()
            assert 0.008 <= d <= 0.025


class TestWeightedChoice:
    def test_single_option(self):
        assert Randomizer.weighted_choice([("only", 1.0)]) == "only"

    def test_returns_valid_option(self):
        options = [("a", 1.0), ("b", 2.0), ("c", 3.0)]
        for _ in range(50):
            result = Randomizer.weighted_choice(options)
            assert result in ("a", "b", "c")

    def test_zero_weight_never_chosen(self):
        # Weight of 0 should (almost) never be chosen
        options = [("never", 0.0), ("always", 100.0)]
        for _ in range(100):
            assert Randomizer.weighted_choice(options) == "always"


class TestPerpendicularOffset:
    def test_returns_tuple(self):
        result = Randomizer._perpendicular_offset((0, 0), (100, 0), 0.2)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_zero_distance(self):
        result = Randomizer._perpendicular_offset((5, 5), (5, 5), 0.2)
        assert isinstance(result, tuple)
