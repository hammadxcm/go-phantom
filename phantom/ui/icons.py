"""Embedded icon for system tray."""

from __future__ import annotations

import base64
import io

from PIL import Image

# 16x16 ghost icon as base64 PNG (minimal, generated programmatically)
_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA3ElEQVQ4y2NgGAUkAEYo"
    "Gw/A0NDQBMTzgfg/EO8H4gZGRsZGXJoZoAb8B+L5UDG4AUBxBhwaGKBe+A/l4zSAkGYG"
    "qBcYsFmAywv/sWlgxBOA/4kJRGwGMODzAi4DiHoBpwH4AhGXAQz4YgGXAUAv/CcUC7gM"
    "YMAXC4RigRHKJ5oGNEDKIIRhCxdsXviPLxYIGcBAKBaISkgGPMkJVywQSkgGfMmJYCwQ"
    "TEgGQslJD4jnA3EDsYmJAV9yIhQLhBKSAV9yYiAYC0QkJAOx5EQoFvAlJwYiEhIA94b0"
    "RBaZpjkAAAAASUVORK5CYII="
)


def create_tray_icon() -> Image.Image:
    """Decode the embedded icon and return a PIL Image."""
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
