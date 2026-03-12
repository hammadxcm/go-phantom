"""Tests for phantom.ui.tail_formatter."""

from __future__ import annotations

import logging

from phantom.ui.ansi import BOLD_RED, BOLD_YELLOW, CYAN, DIM, GREEN, RESET
from phantom.ui.tail_formatter import TailFormatter


def _make_record(name: str, level: int, msg: str) -> logging.LogRecord:
    return logging.LogRecord(
        name=name,
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )


class TestTailFormatter:
    def setup_method(self):
        self.fmt = TailFormatter()

    def test_format_error_level(self):
        record = _make_record("test", logging.ERROR, "something broke")
        result = self.fmt.format(record)
        assert result.startswith(BOLD_RED)
        assert result.endswith(RESET)
        assert "something broke" in result

    def test_format_warning_level(self):
        record = _make_record("test", logging.WARNING, "watch out")
        result = self.fmt.format(record)
        assert result.startswith(BOLD_YELLOW)
        assert result.endswith(RESET)
        assert "watch out" in result

    def test_format_sim_logger_mouse(self):
        record = _make_record("phantom.simulators.mouse", logging.INFO, "moved")
        result = self.fmt.format(record)
        assert result.startswith(CYAN)
        assert result.endswith(RESET)
        assert "moved" in result

    def test_format_sim_logger_keyboard(self):
        record = _make_record("phantom.simulators.keyboard", logging.INFO, "typed")
        result = self.fmt.format(record)
        assert result.startswith(GREEN)
        assert result.endswith(RESET)
        assert "typed" in result

    def test_format_unknown_logger(self):
        record = _make_record("some.other.logger", logging.INFO, "hello")
        result = self.fmt.format(record)
        assert result.startswith(DIM)
        assert result.endswith(RESET)
        assert "hello" in result

    def test_format_includes_timestamp_and_name(self):
        record = _make_record("mylogger", logging.INFO, "test msg")
        result = self.fmt.format(record)
        # Format is "HH:MM:SS name: message"
        assert "mylogger" in result
        assert "test msg" in result
        # Should contain time-like pattern (stripped of ANSI)
        stripped = result.replace(DIM, "").replace(RESET, "")
        assert ":" in stripped  # time separator present
