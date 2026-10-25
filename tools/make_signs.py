"""Dessine les panneaux des murs, en français et en anglais, dans assets/textures/.

Usage :
    python -m tools.make_signs

Les textes viennent de locales/ (clés « sign.* ») : un panneau traduit dans le
jeu l'est aussi sur le mur. Une image par panneau et par langue :
sign_<nom>_<langue>.png.
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
ROOM_PLATE = ((214, 210, 196), (40, 52, 74))  # (fond émaillé, texte bleu nuit)
EXIT_PLATE = (
    (30, 140, 70),
    (236, 244, 236),
)  # (vert de sortie de secours, texte blanc)
EXIT_KEYS = {"sign.exit_right"}


def fit_font(
    draw: ImageDraw.ImageDraw, text: str, max_width: int
) -> ImageFont.ImageFont:
    """La plus grande police dans laquelle le texte tient sur la plaque."""
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
    draw.rectangle((1, 1, width - 2, height - 2), outline=ink)  # liseré
    text_width = width - (34 if is_exit else 12)
    font = fit_font(draw, text, text_width)
    draw.text((6 + text_width / 2, height / 2), text, fill=ink, font=font, anchor="mm")
    if is_exit:  # une flèche vers la droite
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
    for _ in range(140):  # rouille et crasse sur l'émail
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
            print(f"Panneau créé : {name}.png")


if __name__ == "__main__":
    main()
