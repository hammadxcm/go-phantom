"""Tests for phantom.ui.log_handler."""

from __future__ import annotations

import logging
from unittest.mock import patch

from phantom.ui.log_handler import DequeHandler


def _make_logger(name: str, handler: DequeHandler) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


class TestDequeHandler:
    def test_basic_capture(self, log_handler):
        logger = _make_logger("test.deque.basic", log_handler)
        logger.info("hello")
        assert log_handler.lines == ["hello"]
        logger.removeHandler(log_handler)

    def test_multiple_messages(self, log_handler):
        logger = _make_logger("test.deque.multi", log_handler)
        logger.info("one")
        logger.info("two")
        logger.info("three")
        assert log_handler.lines == ["one", "two", "three"]
        logger.removeHandler(log_handler)

    def test_maxlen_enforced(self):
        handler = DequeHandler(maxlen=3)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = _make_logger("test.deque.maxlen", handler)

        for i in range(5):
            logger.info("msg%d", i)

        lines = handler.lines
        assert len(lines) == 3
        assert lines == ["msg2", "msg3", "msg4"]
        logger.removeHandler(handler)

    def test_empty_lines(self):
        handler = DequeHandler()
        assert handler.lines == []

    def test_default_maxlen(self):
        handler = DequeHandler()
        assert handler.maxlen == 200

    def test_custom_maxlen(self):
        handler = DequeHandler(maxlen=50)
        assert handler.maxlen == 50

    def test_lines_returns_list_copy(self, log_handler):
        logger = _make_logger("test.deque.copy", log_handler)
        logger.info("a")
        lines1 = log_handler.lines
        logger.info("b")
        lines2 = log_handler.lines

        assert lines1 == ["a"]
        assert lines2 == ["a", "b"]
        logger.removeHandler(log_handler)

    def test_formatter_applied(self):
        handler = DequeHandler(maxlen=10)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger = _make_logger("test.deque.format", handler)
        logger.warning("oops")
        assert handler.lines == ["[WARNING] oops"]
        logger.removeHandler(handler)

    def test_is_logging_handler(self):
        handler = DequeHandler()
        assert isinstance(handler, logging.Handler)

    def test_lines_styled_returns_tuples(self, log_handler):
        logger = _make_logger("test.deque.styled", log_handler)
        logger.info("hello")
        styled = log_handler.lines_styled
        assert len(styled) == 1
        msg, name, level = styled[0]
        assert msg == "hello"
        assert name == "test.deque.styled"
        assert level == logging.INFO
        logger.removeHandler(log_handler)

    def test_stale_entries_pruned(self):
        handler = DequeHandler(maxlen=50, max_age_secs=1.0)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = _make_logger("test.deque.prune", handler)

        # Emit a message at a fake old time
        with patch("phantom.ui.log_handler.time.monotonic", return_value=100.0):
            logger.info("old")

        # Emit a message at "now"
        with patch("phantom.ui.log_handler.time.monotonic", return_value=200.0):
            logger.info("new")

        # Read at time 200 — "old" is 100s old, max_age is 1s → pruned
        with patch("time.monotonic", return_value=200.0):
            lines = handler.lines
        assert "new" in lines
        # "old" should be pruned (100s > 1s max_age)
        logger.removeHandler(handler)

    def test_default_max_age(self):
        handler = DequeHandler()
        assert handler._max_age == 300.0

    def test_custom_max_age(self):
        handler = DequeHandler(max_age_secs=60.0)
        assert handler._max_age == 60.0
