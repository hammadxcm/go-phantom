"""Tests for phantom.ui.icons."""

from __future__ import annotations

import base64

from PIL import Image

from phantom.ui.icons import _ICON_B64, create_status_icon, create_tray_icon


class TestCreateTrayIcon:
    def test_returns_image(self):
        img = create_tray_icon()
        assert isinstance(img, Image.Image)

    def test_image_dimensions(self):
        img = create_tray_icon()
        assert img.size == (64, 64)

    def test_image_mode(self):
        img = create_tray_icon()
        assert img.mode in ("RGBA", "RGB")

    def test_not_blank(self):
        img = create_tray_icon().convert("RGBA")
        extrema = img.getextrema()
        has_content = any(ch[1] > 0 for ch in extrema)
        assert has_content

    def test_idempotent(self):
        """Calling create_tray_icon twice returns identical images."""
        img1 = create_tray_icon().convert("RGBA")
        img2 = create_tray_icon().convert("RGBA")
        assert img1.tobytes() == img2.tobytes()


class TestIconBase64:
    def test_valid_base64(self):
        data = base64.b64decode(_ICON_B64)
        assert len(data) > 0

    def test_valid_png_header(self):
        data = base64.b64decode(_ICON_B64)
        # PNG magic bytes
        assert data[:4] == b"\x89PNG"


class TestCreateStatusIcon:
    def test_active_icon(self):
        img = create_status_icon(True)
        assert isinstance(img, Image.Image)
        assert img.size == (64, 64)
        assert img.mode == "RGBA"
        # Center pixel should be green
        cx, cy = 32, 32
        r, g, _b, a = img.getpixel((cx, cy))
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
        _r, _g, _b, a = img.getpixel((0, 0))
        assert a == 0

    def test_active_and_paused_differ(self):
        active = create_status_icon(True)
        paused = create_status_icon(False)
        assert active.tobytes() != paused.tobytes()

    def test_circle_boundary(self):
        """Pixels just outside the circle radius should be transparent."""
        img = create_status_icon(True)
        # Top-left corner at (1, 1) is outside the circle
        _r, _g, _b, a = img.getpixel((1, 1))
        assert a == 0

    def test_dimensions_consistent(self):
        for active in (True, False):
            img = create_status_icon(active)
            assert img.size == (64, 64)
            assert img.mode == "RGBA"
