"""Generates placeholder icon assets (no real brand assets were supplied).

Draws a simple rounded-square gradient "FB" monogram and saves it as both a PNG (for
in-app CTkImage use) and a multi-size ICO (for the PyInstaller exe icon / Inno Setup
installer icon). Safe to re-run - regenerates deterministically.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
ICONS_DIR = REPO_ROOT / "assets" / "icons"

_SIZE = 512
_BG_TOP = (108, 92, 231)  # matches ui.theme.ACCENT
_BG_BOTTOM = (0, 210, 255)
_TEXT_COLOR = (255, 255, 255)


def _rounded_gradient_square(size: int) -> Image.Image:
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gradient = Image.new("RGBA", (size, size))
    for y in range(size):
        t = y / max(1, size - 1)
        color = tuple(int(_BG_TOP[i] + (_BG_BOTTOM[i] - _BG_TOP[i]) * t) for i in range(3)) + (255,)
        for x in range(size):
            gradient.putpixel((x, y), color)

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    radius = int(size * 0.22)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)

    base.paste(gradient, (0, 0), mask)
    return base


def _draw_monogram(image: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(image)
    text = "FB"
    try:
        font = ImageFont.truetype("segoeuib.ttf", int(image.width * 0.42))
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    position = ((image.width - text_w) / 2 - bbox[0], (image.height - text_h) / 2 - bbox[1])
    draw.text(position, text, font=font, fill=_TEXT_COLOR)
    return image


def generate() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    icon = _draw_monogram(_rounded_gradient_square(_SIZE))

    png_path = ICONS_DIR / "app.png"
    icon.save(png_path)

    ico_path = ICONS_DIR / "app.ico"
    icon.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (128, 128), (256, 256)])

    print(f"Generated {png_path}")
    print(f"Generated {ico_path}")


if __name__ == "__main__":
    sys.exit(generate() or 0)
