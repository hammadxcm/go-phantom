"""Embedded icon for system tray."""

from __future__ import annotations

import base64
import io

from PIL import Image

# 64x64 brand icon as base64 PNG (generated from assets/icon.svg)
_ICON_B64 = (
    "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"
    "YII="
)


def create_tray_icon() -> Image.Image:
    """Decode the embedded brand icon and return a PIL Image."""
    data = base64.b64decode(_ICON_B64)
    return Image.open(io.BytesIO(data))


def create_status_icon(active: bool) -> Image.Image:
    """Create a colored status icon. Green=active, gray=paused."""
    size = 64
    color = (76, 175, 80, 255) if active else (158, 158, 158, 255)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # Draw a filled circle
    for x in range(size):
        for y in range(size):
            cx, cy = size // 2, size // 2
            if (x - cx) ** 2 + (y - cy) ** 2 <= (size // 2 - 2) ** 2:
                img.putpixel((x, y), color)
    return img
