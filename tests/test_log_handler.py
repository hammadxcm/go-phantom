"""Tests for phantom.ui.log_handler."""

from __future__ import annotations

import logging

from phantom.ui.log_handler import DequeHandler


class TestDequeHandler:
    def test_basic_capture(self):
        handler = DequeHandler(maxlen=10)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.deque.basic")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("hello")
        assert handler.lines == ["hello"]

        logger.removeHandler(handler)

    def test_multiple_messages(self):
        handler = DequeHandler(maxlen=10)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.deque.multi")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("one")
        logger.info("two")
        logger.info("three")
        assert handler.lines == ["one", "two", "three"]

        logger.removeHandler(handler)

    def test_maxlen_enforced(self):
        handler = DequeHandler(maxlen=3)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.deque.maxlen")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

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

    def test_lines_returns_list_copy(self):
        handler = DequeHandler(maxlen=10)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger = logging.getLogger("test.deque.copy")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("a")
        lines1 = handler.lines
        logger.info("b")
        lines2 = handler.lines

        assert lines1 == ["a"]
        assert lines2 == ["a", "b"]

        logger.removeHandler(handler)

    def test_formatter_applied(self):
        handler = DequeHandler(maxlen=10)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger = logging.getLogger("test.deque.format")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.warning("oops")
        assert handler.lines == ["[WARNING] oops"]

        logger.removeHandler(handler)

    def test_is_logging_handler(self):
        handler = DequeHandler()
        assert isinstance(handler, logging.Handler)
