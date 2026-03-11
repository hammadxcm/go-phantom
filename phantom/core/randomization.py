"""Human-like randomization: Bezier curves, statistical distributions, timing."""

from __future__ import annotations

import math
import random

Point = tuple[float, float]


class Randomizer:
    """Generates human-like random values for movement, timing, and selection."""

    # Mouse path constants
    CONTROL_POINT_OFFSET_MIN = 0.05
    CONTROL_POINT_OFFSET_MAX = 0.20
    NOISE_SIGMA_MIN = 0.3
    NOISE_SIGMA_MAX = 1.0

    # Timing constants
    DEFAULT_INTERVAL_MEAN = 8.0
    DEFAULT_INTERVAL_STDDEV = 4.0
    DEFAULT_INTERVAL_MIN = 0.5
    IDLE_CHANCE = 0.10
    IDLE_MIN = 15.0
    IDLE_MAX = 120.0

    # Keystroke constants
    KEYSTROKE_BASE_MIN = 0.05
    KEYSTROKE_BASE_MAX = 0.20
    THINKING_PAUSE_CHANCE = 0.05
    THINKING_PAUSE_MIN = 0.30
    THINKING_PAUSE_MAX = 0.80

    @staticmethod
    def bezier_point(t: float, p0: Point, p1: Point, p2: Point, p3: Point) -> Point:
        """Evaluate a cubic Bezier curve at parameter t."""
        u = 1.0 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        return (x, y)

    @staticmethod
    def _perpendicular_offset(
        start: Point, end: Point, fraction: float
    ) -> Point:
        """Generate a control point offset perpendicular to the line."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = math.hypot(dx, dy) or 1.0
        offset = dist * fraction * random.choice([-1, 1])
        # Perpendicular direction: rotate (dx, dy) by 90 degrees
        px = -dy / dist * offset
        py = dx / dist * offset
        return (px, py)

    @classmethod
    def bezier_control_points(cls, start: Point, end: Point) -> tuple[Point, Point]:
        """Generate two random control points for a cubic Bezier between start and end."""
        cp1_frac = random.uniform(cls.CONTROL_POINT_OFFSET_MIN, cls.CONTROL_POINT_OFFSET_MAX)
        cp2_frac = random.uniform(cls.CONTROL_POINT_OFFSET_MIN, cls.CONTROL_POINT_OFFSET_MAX)

        off1 = cls._perpendicular_offset(start, end, cp1_frac)
        off2 = cls._perpendicular_offset(start, end, cp2_frac)

        # Place control points at ~1/3 and ~2/3 along the line
        t1, t2 = random.uniform(0.2, 0.4), random.uniform(0.6, 0.8)
        mid1 = (start[0] + (end[0] - start[0]) * t1, start[1] + (end[1] - start[1]) * t1)
        mid2 = (start[0] + (end[0] - start[0]) * t2, start[1] + (end[1] - start[1]) * t2)

        cp1 = (mid1[0] + off1[0], mid1[1] + off1[1])
        cp2 = (mid2[0] + off2[0], mid2[1] + off2[1])
        return cp1, cp2

    @staticmethod
    def _ease_in_out(t: float) -> float:
        """Smooth ease-in-out curve: slow start, fast middle, slow end."""
        return t * t * (3.0 - 2.0 * t)

    @classmethod
    def bezier_path(cls, start: Point, end: Point, steps: int = 50) -> list[Point]:
        """Generate a human-like Bezier mouse path from start to end."""
        cp1, cp2 = cls.bezier_control_points(start, end)
        sigma = random.uniform(cls.NOISE_SIGMA_MIN, cls.NOISE_SIGMA_MAX)
        path: list[Point] = []
        for i in range(steps + 1):
            # Apply ease-in-out so cursor accelerates then decelerates
            t = cls._ease_in_out(i / steps)
            x, y = cls.bezier_point(t, start, cp1, cp2, end)
            # Light noise in the middle of the path only, fade near endpoints
            if 0 < i < steps:
                fade = 1.0 - abs(2.0 * i / steps - 1.0)  # 0→1→0 triangle
                x += random.gauss(0, sigma * fade)
                y += random.gauss(0, sigma * fade)
            path.append((round(x), round(y)))
        return path

    @classmethod
    def action_interval(
        cls,
        mean: float = DEFAULT_INTERVAL_MEAN,
        stddev: float = DEFAULT_INTERVAL_STDDEV,
        minimum: float = DEFAULT_INTERVAL_MIN,
    ) -> float:
        """Return a gaussian-distributed action interval in seconds."""
        return max(minimum, random.gauss(mean, stddev))

    @classmethod
    def should_idle(cls) -> bool:
        return random.random() < cls.IDLE_CHANCE

    @classmethod
    def idle_duration(cls) -> float:
        """Exponential-distributed idle duration between IDLE_MIN and IDLE_MAX."""
        raw = random.expovariate(1.0 / 30.0)
        return max(cls.IDLE_MIN, min(cls.IDLE_MAX, raw + cls.IDLE_MIN))

    @classmethod
    def keystroke_delay(cls) -> float:
        """Human-like delay between keystrokes."""
        base = random.uniform(cls.KEYSTROKE_BASE_MIN, cls.KEYSTROKE_BASE_MAX)
        if random.random() < cls.THINKING_PAUSE_CHANCE:
            base += random.uniform(cls.THINKING_PAUSE_MIN, cls.THINKING_PAUSE_MAX)
        return base

    @classmethod
    def step_delay(cls) -> float:
        """Delay between individual mouse movement steps (8-25ms)."""
        return random.uniform(0.008, 0.025)

    @staticmethod
    def weighted_choice(options: list[tuple[str, float]]) -> str:
        """Weighted random selection. Returns the chosen option name."""
        names, weights = zip(*options)
        return random.choices(list(names), weights=list(weights), k=1)[0]
