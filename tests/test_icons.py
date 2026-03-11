"""Tests for phantom.ui.icons."""

from __future__ import annotations

from PIL import Image

from phantom.ui.icons import create_status_icon, create_tray_icon


class TestCreateTrayIcon:
    def test_returns_image(self):
        img = create_tray_icon()
        assert isinstance(img, Image.Image)

    def test_image_dimensions(self):
        img = create_tray_icon()
        assert img.size == (16, 16)


class TestCreateStatusIcon:
    def test_active_icon(self):
        img = create_status_icon(True)
        assert isinstance(img, Image.Image)
        assert img.size == (64, 64)
        assert img.mode == "RGBA"
        # Center pixel should be green
        cx, cy = 32, 32
        r, g, b, a = img.getpixel((cx, cy))
        assert g > r  # Green component dominant
        assert a == 255

    def test_paused_icon(self):
        img = create_status_icon(False)
        assert isinstance(img, Image.Image)
        cx, cy = 32, 32
        r, g, b, a = img.getpixel((cx, cy))
        assert r == g == b == 158  # Gray
        assert a == 255

    def test_corner_is_transparent(self):
        img = create_status_icon(True)
        r, g, b, a = img.getpixel((0, 0))
        assert a == 0
