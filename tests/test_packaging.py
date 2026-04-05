"""Tests for packaging files: .desktop entries, postinst, snapcraft, PyInstaller spec."""

from __future__ import annotations

import configparser
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


class TestLinuxDesktopEntry:
    """Validate packaging/linux/phantom.desktop per freedesktop.org spec."""

    @pytest.fixture
    def desktop(self):
        path = ROOT / "packaging" / "linux" / "phantom.desktop"
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(str(path))
        return cp

    def test_file_exists(self):
        assert (ROOT / "packaging" / "linux" / "phantom.desktop").exists()

    def test_has_desktop_entry_section(self, desktop):
        assert "Desktop Entry" in desktop.sections()

    def test_name(self, desktop):
        assert desktop.get("Desktop Entry", "Name") == "Phantom"

    def test_exec(self, desktop):
        assert desktop.get("Desktop Entry", "Exec") == "phantom --gui"

    def test_icon(self, desktop):
        assert desktop.get("Desktop Entry", "Icon") == "phantom"

    def test_type(self, desktop):
        assert desktop.get("Desktop Entry", "Type") == "Application"

    def test_terminal_false(self, desktop):
        assert desktop.get("Desktop Entry", "Terminal") == "false"

    def test_categories(self, desktop):
        cats = desktop.get("Desktop Entry", "Categories")
        assert "Utility" in cats

    def test_startup_notify(self, desktop):
        assert desktop.get("Desktop Entry", "StartupNotify") == "false"

    def test_comment(self, desktop):
        comment = desktop.get("Desktop Entry", "Comment")
        assert len(comment) > 0


class TestSnapDesktopEntry:
    """Validate snap/gui/phantom.desktop."""

    @pytest.fixture
    def desktop(self):
        path = ROOT / "snap" / "gui" / "phantom.desktop"
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(str(path))
        return cp

    def test_file_exists(self):
        assert (ROOT / "snap" / "gui" / "phantom.desktop").exists()

    def test_has_desktop_entry_section(self, desktop):
        assert "Desktop Entry" in desktop.sections()

    def test_name(self, desktop):
        assert desktop.get("Desktop Entry", "Name") == "Phantom"

    def test_exec(self, desktop):
        assert desktop.get("Desktop Entry", "Exec") == "phantom --gui"

    def test_icon_uses_snap_variable(self, desktop):
        icon = desktop.get("Desktop Entry", "Icon")
        assert "${SNAP}" in icon
        assert "icon.png" in icon

    def test_type(self, desktop):
        assert desktop.get("Desktop Entry", "Type") == "Application"

    def test_terminal_false(self, desktop):
        assert desktop.get("Desktop Entry", "Terminal") == "false"


class TestPostInstScript:
    """Validate packaging/linux/postinst.sh."""

    @pytest.fixture
    def script_path(self):
        return ROOT / "packaging" / "linux" / "postinst.sh"

    def test_file_exists(self, script_path):
        assert script_path.exists()

    def test_is_executable(self, script_path):
        assert os.access(script_path, os.X_OK)

    def test_has_shebang(self, script_path):
        first_line = script_path.read_text().splitlines()[0]
        assert first_line.startswith("#!/bin/sh")

    def test_updates_icon_cache(self, script_path):
        content = script_path.read_text()
        assert "gtk-update-icon-cache" in content

    def test_updates_desktop_database(self, script_path):
        content = script_path.read_text()
        assert "update-desktop-database" in content

    def test_errors_suppressed(self, script_path):
        content = script_path.read_text()
        # Each command should have || true for graceful failure
        assert "|| true" in content


class TestSnapcraftYaml:
    """Validate snap/snapcraft.yaml structure."""

    @pytest.fixture
    def snapcraft(self):
        import yaml

        path = ROOT / "snap" / "snapcraft.yaml"
        return yaml.safe_load(path.read_text())

    def test_file_exists(self):
        assert (ROOT / "snap" / "snapcraft.yaml").exists()

    def test_has_icon_field(self):
        """Check icon field exists in raw text (no yaml dependency needed)."""
        content = (ROOT / "snap" / "snapcraft.yaml").read_text()
        assert "icon:" in content
        assert "icon-256.png" in content

    def test_name(self):
        content = (ROOT / "snap" / "snapcraft.yaml").read_text()
        assert "name: go-phantom" in content

    def test_confinement(self):
        content = (ROOT / "snap" / "snapcraft.yaml").read_text()
        assert "confinement: strict" in content


class TestPyInstallerSpec:
    """Validate build/phantom.spec configuration."""

    @pytest.fixture
    def spec_content(self):
        return (ROOT / "build" / "phantom.spec").read_text()

    def test_file_exists(self):
        assert (ROOT / "build" / "phantom.spec").exists()

    def test_has_icon_parameter(self, spec_content):
        assert "icon=" in spec_content

    def test_icon_points_to_ico(self, spec_content):
        assert "phantom.ico" in spec_content

    def test_entry_point(self, spec_content):
        assert "__main__.py" in spec_content

    def test_console_false(self, spec_content):
        assert "console=False" in spec_content

    def test_hidden_imports(self, spec_content):
        assert "pynput" in spec_content
        assert "pystray" in spec_content
        assert "tkinter" in spec_content

    def test_data_files(self, spec_content):
        assert "defaults.json" in spec_content


class TestReleaseWorkflow:
    """Validate .github/workflows/release.yml deb packaging."""

    @pytest.fixture
    def workflow(self):
        return (ROOT / ".github" / "workflows" / "release.yml").read_text()

    def test_file_exists(self):
        assert (ROOT / ".github" / "workflows" / "release.yml").exists()

    def test_deb_uses_staging(self, workflow):
        assert "staging/usr/bin" in workflow

    def test_deb_includes_desktop_entry(self, workflow):
        assert "phantom.desktop" in workflow
        assert "staging/usr/share/applications" in workflow

    def test_deb_includes_icons(self, workflow):
        assert "hicolor" in workflow
        assert "icon-${size}.png" in workflow

    def test_deb_uses_postinst(self, workflow):
        assert "--after-install" in workflow
        assert "postinst.sh" in workflow

    def test_deb_has_maintainer(self, workflow):
        assert "--maintainer" in workflow

    def test_deb_has_url(self, workflow):
        assert "--url" in workflow

    def test_deb_has_category(self, workflow):
        assert "--category" in workflow


class TestAssetDirectory:
    """Verify the assets/ directory is complete and consistent."""

    def test_directory_exists(self):
        assert (ROOT / "assets").is_dir()

    def test_svg_matches_source(self):
        """assets/icon.svg should match phantom-macos/icon.svg."""
        src = (ROOT / "phantom-macos" / "icon.svg").read_text()
        dst = (ROOT / "assets" / "icon.svg").read_text()
        assert src == dst

    def test_all_required_files_present(self):
        required = [
            "icon.svg",
            "icon.png",
            "phantom.ico",
            "phantom.icns",
        ]
        for name in required:
            assert (ROOT / "assets" / name).exists(), f"Missing: {name}"

    def test_png_sizes_complete(self):
        for size in [16, 32, 48, 64, 128, 256, 512, 1024]:
            path = ROOT / "assets" / f"icon-{size}.png"
            assert path.exists(), f"Missing: icon-{size}.png"
            assert path.stat().st_size > 0
