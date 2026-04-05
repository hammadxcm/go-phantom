"""Tests for scripts/generate_icons.py."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SCRIPT = ROOT / "scripts" / "generate_icons.py"


@pytest.fixture
def gen_icons():
    """Import generate_icons as a module."""
    spec = importlib.util.spec_from_file_location("generate_icons", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestGenerateIconsConstants:
    def test_sizes_list(self, gen_icons):
        assert gen_icons.SIZES == [16, 32, 48, 64, 128, 256, 512, 1024]

    def test_ico_sizes_subset(self, gen_icons):
        for s in gen_icons.ICO_SIZES:
            assert s in gen_icons.SIZES

    def test_root_path(self, gen_icons):
        assert gen_icons.ROOT == ROOT

    def test_assets_path(self, gen_icons):
        assert gen_icons.ASSETS == ASSETS

    def test_svg_path(self, gen_icons):
        assert gen_icons.SVG == ASSETS / "icon.svg"


class TestGeneratedAssets:
    """Verify that the generated assets actually exist and are valid."""

    def test_svg_exists(self):
        assert (ASSETS / "icon.svg").exists()

    def test_icon_png_exists(self):
        assert (ASSETS / "icon.png").exists()

    def test_ico_exists(self):
        assert (ASSETS / "phantom.ico").exists()

    def test_icns_exists(self):
        assert (ASSETS / "phantom.icns").exists()

    @pytest.mark.parametrize("size", [16, 32, 48, 64, 128, 256, 512, 1024])
    def test_png_exists(self, size):
        assert (ASSETS / f"icon-{size}.png").exists()

    @pytest.mark.parametrize("size", [16, 32, 48, 64, 128, 256, 512, 1024])
    def test_png_dimensions(self, size):
        from PIL import Image

        img = Image.open(ASSETS / f"icon-{size}.png")
        assert img.size == (size, size)

    def test_icon_png_is_256(self):
        from PIL import Image

        img = Image.open(ASSETS / "icon.png")
        assert img.size == (256, 256)

    def test_ico_is_valid(self):
        from PIL import Image

        img = Image.open(ASSETS / "phantom.ico")
        assert img.format == "ICO"

    def test_ico_has_multiple_sizes(self):
        # ICO file should have content > single 16x16 PNG
        ico_path = ASSETS / "phantom.ico"
        assert ico_path.stat().st_size > 100

    def test_icns_has_valid_header(self):
        data = (ASSETS / "phantom.icns").read_bytes()
        # ICNS magic bytes: 'icns'
        assert data[:4] == b"icns"


class TestRenderPng:
    def test_renders_valid_image(self, gen_icons):
        img = gen_icons.render_png(32)
        assert img.size == (32, 32)

    def test_renders_at_requested_size(self, gen_icons):
        for size in [16, 64, 128]:
            img = gen_icons.render_png(size)
            assert img.size == (size, size)
