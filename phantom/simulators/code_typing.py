"""Simulated code typing — types realistic code snippets character by character."""

from __future__ import annotations

import logging
import random
import time
from pathlib import Path

from pynput.keyboard import Controller

from phantom.config.schema import CodeTypingConfig
from phantom.core.randomization import Randomizer
from phantom.simulators.base import BaseSimulator

_log = logging.getLogger(__name__)

# Short, realistic code fragments across common languages.
# Each snippet is self-contained and harmless if typed into an editor.
_CODE_SNIPPETS = [
    "const data = await fetch(url);",
    "if err != nil { return err }",
    "for i in range(len(items)):",
    "    result.append(transform(x))",
    "fn main() -> Result<()> {",
    "let mut count = 0;",
    "SELECT id, name FROM users WHERE active = true;",
    "export default function App() {",
    "return json.dumps(response)",
    "console.log('debug:', value);",
    "def process(data: list[str]) -> dict:",
    "    return {k: v for k, v in pairs}",
    "import { useState, useEffect } from 'react';",
    "class Handler(BaseHandler):",
    "func (s *Server) Listen(port int) error {",
    "docker compose up -d --build",
    "git commit -m 'fix: resolve edge case'",
    "npm install --save-dev typescript",
    "kubectl get pods -n production",
    "ssh user@host -p 2222",
    "grep -rn 'TODO' src/",
    "pytest -x --cov=app tests/",
    "curl -s http://localhost:8080/health",
    "    logger.info('request processed in %dms', elapsed)",
    "type Config struct {",
    '    Host string `json:"host"`',
    "}",
    "async function handleRequest(req: Request) {",
    "    const body = await req.json();",
    "impl Display for Error {",
    "    fn fmt(&self, f: &mut Formatter) -> fmt::Result {",
    "map(lambda x: x * 2, numbers)",
    "Object.keys(config).forEach(key => {",
    "    services.AddScoped<IRepository, Repository>();",
    "echo $PATH | tr ':' '\\n'",
    "awk '{print $1, $NF}' access.log",
    "sed -i 's/old/new/g' config.yaml",
    "    assert response.status_code == 200",
    "CREATE INDEX idx_users_email ON users(email);",
    "ALTER TABLE orders ADD COLUMN status VARCHAR(20);",
    "    this.setState({ loading: true });",
    "const router = express.Router();",
    "app.get('/api/v1/users', authenticate, getUsers);",
    "FROM python:3.12-slim AS builder",
    "RUN pip install --no-cache-dir -r requirements.txt",
    "EXPOSE 8080",
    "ENV NODE_ENV=production",
]


def _load_file_lines(path: str) -> list[str]:
    """Read non-empty lines from a text file.

    Args:
        path: Filesystem path to the source file.

    Returns:
        List of stripped, non-empty lines. Empty list on any error.
    """
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        return [line for line in text.splitlines() if line.strip()]
    except OSError as exc:
        _log.warning("Cannot read source_file %r: %s", path, exc)
        return []


class CodeTypingSimulator(BaseSimulator):
    """Types realistic code snippets character by character.

    Simulates a developer actively writing code by typing random code
    fragments with human-like inter-keystroke timing.  When ``source_file``
    is set in config, reads lines from that text file instead of using
    built-in snippets.  Controlled by a dedicated hotkey (Ctrl+Alt+T).
    """

    def __init__(self) -> None:
        """Initialize the code typing simulator with a pynput controller."""
        super().__init__()
        self._controller = Controller()
        self._file_lines: list[str] = []
        self._loaded_path: str = ""

    def _get_snippets(self, config: CodeTypingConfig) -> list[str]:
        """Return the snippet pool, loading from file if configured."""
        if config.source_file:
            # Reload if path changed
            if config.source_file != self._loaded_path:
                self._file_lines = _load_file_lines(config.source_file)
                self._loaded_path = config.source_file
                if self._file_lines:
                    self.log.info(
                        "Loaded %d lines from %s",
                        len(self._file_lines),
                        config.source_file,
                    )
            if self._file_lines:
                return self._file_lines
        return _CODE_SNIPPETS

    def execute(self, config: CodeTypingConfig) -> str:
        """Type a random code snippet character by character.

        Args:
            config: Code typing simulator configuration.

        Returns:
            Detail string describing what was typed.
        """
        snippets = self._get_snippets(config)
        snippet = random.choice(snippets)

        # Truncate or select portion based on config limits
        max_len = random.randint(config.min_chars, config.max_chars)
        text = snippet[:max_len]

        for char in text:
            self._controller.type(char)
            delay = random.uniform(config.char_delay_min, config.char_delay_max)
            # Occasional thinking pause (5% chance)
            if random.random() < 0.05:
                delay += random.uniform(0.3, 0.8)
            time.sleep(delay)

        # Add trailing keystroke delay
        time.sleep(Randomizer.keystroke_delay())

        used_file = config.source_file and snippets is not _CODE_SNIPPETS
        source = Path(config.source_file).name if used_file else "built-in"
        preview = text[:40] + ("..." if len(text) > 40 else "")
        detail = f"Code typed {len(text)} chars ({source}): {preview!r}"
        self.log.info(detail)
        return detail
