"""Draws the wall signs, in French and English, into assets/textures/.

Usage:
    python -m tools.make_signs

Texts come from locales/ ("sign.*" keys): a sign translated in the game is
translated on the wall too. One image per sign and per language:
sign_<name>_<language>.png.
"""

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ROOT / "locales"
OUTPUT = ROOT / "assets" / "textures"
SIZE = (128, 32)
SEED = 21
ROOM_PLATE = ((214, 210, 196), (40, 52, 74))  # (enamel background, navy text)
EXIT_PLATE = (
    (30, 140, 70),
    (236, 244, 236),
)  # (emergency exit green, white text)
EXIT_KEYS = {"sign.exit_right"}


def fit_font(
    draw: ImageDraw.ImageDraw, text: str, max_width: int
) -> ImageFont.ImageFont:
    """The largest font in which the text fits on the plate."""
    for size in range(20, 7, -1):
        font = ImageFont.load_default(size=size)
        if draw.textlength(text, font=font) <= max_width:
            return font
    return ImageFont.load_default(size=8)


def draw_sign(text: str, is_exit: bool, rng: random.Random) -> Image.Image:
    background, ink = EXIT_PLATE if is_exit else ROOM_PLATE
    image = Image.new("RGB", SIZE, background)
    draw = ImageDraw.Draw(image)
    width, height = SIZE
    draw.rectangle((1, 1, width - 2, height - 2), outline=ink)  # border
    text_width = width - (34 if is_exit else 12)
    font = fit_font(draw, text, text_width)
    draw.text((6 + text_width / 2, height / 2), text, fill=ink, font=font, anchor="mm")
    if is_exit:  # an arrow pointing right
        draw.polygon(
            [
                (width - 26, 11),
                (width - 14, 11),
                (width - 14, 6),
                (width - 6, 16),
                (width - 14, 26),
                (width - 14, 21),
                (width - 26, 21),
            ],
            fill=ink,
        )
    pixels = image.load()
    for _ in range(140):  # rust and grime on the enamel
        x, y = rng.randrange(width), rng.randrange(height)
        red, green, blue = pixels[x, y]
        pixels[x, y] = (
            int(red * 0.75 + 30),
            int(green * 0.7 + 18),
            int(blue * 0.65 + 8),
        )
    return image


def main() -> None:
    rng = random.Random(SEED)
    for path in sorted(LOCALES.glob("*.json")):
        language = path.stem
        catalog = json.loads(path.read_text(encoding="utf-8"))
        for key, text in sorted(catalog.items()):
            if not key.startswith("sign."):
                continue
            name = f"sign_{key.removeprefix('sign.')}_{language}"
            draw_sign(text, key in EXIT_KEYS, rng).save(OUTPUT / f"{name}.png")
            print(f"Sign created: {name}.png")


if __name__ == "__main__":
    main()
