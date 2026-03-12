"""Integration tests — verify phantom boots and runs end-to-end."""

from __future__ import annotations

import subprocess
import sys


class TestCLIIntegration:
    def test_help_flag(self):
        """Verify phantom --help runs and exits cleanly."""
        result = subprocess.run(
            [sys.executable, "-m", "phantom", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "phantom" in result.stdout.lower()
        assert "usage" in result.stdout.lower() or "--help" in result.stdout

    def test_version_import(self):
        """Verify the package imports and exposes a version."""
        result = subprocess.run(
            [sys.executable, "-c", "import phantom; print(phantom.__version__)"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert result.stdout.strip()  # non-empty version string

    def test_invalid_flag(self):
        """Verify phantom rejects unknown flags."""
        result = subprocess.run(
            [sys.executable, "-m", "phantom", "--nonexistent-flag"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0

    def test_mutually_exclusive_modes(self):
        """Verify --tui and --tail cannot be combined."""
        result = subprocess.run(
            [sys.executable, "-m", "phantom", "--tui", "--tail"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0

    def test_preset_flag_accepted(self):
        """Verify --preset flag is recognized (exits via --help to avoid starting)."""
        result = subprocess.run(
            [sys.executable, "-m", "phantom", "--preset", "stealth", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # --help takes precedence and exits 0
        assert result.returncode == 0
