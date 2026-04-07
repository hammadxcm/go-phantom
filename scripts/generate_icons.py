#!/usr/bin/env python3
"""Generate multi-size PNG, ICO, and ICNS icons from the source SVG."""

from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image

try:
    import cairosvg
except ImportError:
    cairosvg = None

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SVG = ASSETS / "icon.svg"

SIZES = [16, 32, 48, 64, 128, 256, 512, 1024]
ICO_SIZES = [16, 32, 48, 64, 128, 256]


def render_png(size: int) -> Image.Image:
    """Render the SVG at the given pixel size and return a PIL Image."""
    import io

    if cairosvg is not None:
        png_data = cairosvg.svg2png(
            url=str(SVG), output_width=size, output_height=size
        )
        return Image.open(io.BytesIO(png_data)).convert("RGBA")

    # Fallback: rasterize with Pillow (lower quality but no native deps)
    svg_png = ASSETS / "icon.png"
    if svg_png.exists():
        img = Image.open(svg_png).convert("RGBA")
        return img.resize((size, size), Image.LANCZOS)

    raise RuntimeError("cairosvg not installed and no fallback icon.png found")


def _build_icns(images: dict[int, Image.Image], out: Path) -> None:
    """Build a minimal ICNS file from a dict of {size: Image}."""
    ostype_map = {
        16: b"icp4",
        32: b"icp5",
        64: b"icp6",
        128: b"ic07",
        256: b"ic08",
        512: b"ic09",
        1024: b"ic10",
    }
    entries = []
    for size, img in sorted(images.items()):
        tag = ostype_map.get(size)
        if tag is None:
            continue
        import io

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_data = buf.getvalue()
        entry = tag + struct.pack(">I", len(png_data) + 8) + png_data
        entries.append(entry)

    body = b"".join(entries)
    header = b"icns" + struct.pack(">I", len(body) + 8)
    out.write_bytes(header + body)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    # Copy SVG into assets
    src_svg = ROOT / "phantom-macos" / "icon.svg"
    if src_svg.exists() and (not SVG.exists() or SVG.read_bytes() != src_svg.read_bytes()):
        SVG.write_bytes(src_svg.read_bytes())

    images: dict[int, Image.Image] = {}
    for size in SIZES:
        img = render_png(size)
        img.save(ASSETS / f"icon-{size}.png")
        images[size] = img

    # icon.png is the 256px version
    images[256].save(ASSETS / "icon.png")

    # ICO
    ico_images = [images[s] for s in ICO_SIZES]
    ico_images[0].save(
        ASSETS / "phantom.ico",
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=ico_images[1:],
    )

    # ICNS
    _build_icns(images, ASSETS / "phantom.icns")

    print(f"Generated icons in {ASSETS}")


if __name__ == "__main__":
    main()
