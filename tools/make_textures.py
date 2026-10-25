"""Génère les textures du bâtiment (style PS1, 64 pixels) dans assets/textures/.

Usage :
    python -m tools.make_textures

Les textures sont dessinées par ce script, pixel par pixel : aucune image
téléchargée, donc aucune licence à créditer. Le hasard est fixé (SEED) :
relancer le script redonne exactement les mêmes images.
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw

OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "textures"
SEED = 7
SIZE = 64  # une case du jeu = 64 pixels de large
WALL_HEIGHT_PIXELS = 192  # le mur fait 3 cases de haut

Color = tuple[int, int, int]


def vary(rng: random.Random, base: Color, amount: int) -> Color:
    """La même couleur, légèrement plus claire ou plus sombre."""
    shift = rng.randint(-amount, amount)
    return tuple(max(0, min(255, channel + shift)) for channel in base)


def add_noise(image: Image.Image, rng: random.Random, amount: int) -> None:
    """Un grain fin sur toute l'image, pour casser les aplats."""
    pixels = image.load()
    for x in range(image.width):
        for y in range(image.height):
            pixels[x, y] = vary(rng, pixels[x, y], amount)


def add_stains(image: Image.Image, rng: random.Random, count: int, dark: Color) -> None:
    """Des taches sombres et irrégulières : la saleté de six ans d'abandon."""
    pixels = image.load()
    for _ in range(count):
        cx, cy = rng.randrange(image.width), rng.randrange(image.height)
        radius = rng.randint(4, 10)
        for x in range(cx - radius, cx + radius + 1):
            for y in range(cy - radius, cy + radius + 1):
                distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if distance > radius or rng.random() < 0.25:
                    continue
                strength = 0.35 * (1 - distance / radius)  # plus pâle sur les bords
                px, py = x % image.width, y % image.height  # la tache se raccorde
                pixels[px, py] = _blend(pixels[px, py], dark, strength)


def _blend(color: Color, other: Color, ratio: float) -> Color:
    return tuple(int(a * (1 - ratio) + b * ratio) for a, b in zip(color, other))


def tiles(
    image: Image.Image,
    rng: random.Random,
    area: tuple[int, int, int, int],
    tile: int,
    base: Color,
    grout: Color,
) -> None:
    """Un carrelage : des carreaux de teinte variable, séparés par des joints."""
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = area
    for x in range(left, right, tile):
        for y in range(top, bottom, tile):
            draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=vary(rng, base, 10))
            draw.line((x, y, x + tile - 1, y), fill=grout)  # joint du haut
            draw.line((x, y, x, y + tile - 1), fill=grout)  # joint de gauche


def make_floor(rng: random.Random) -> Image.Image:
    """Carrelage d'hôpital gris-blanc, 4 x 4 carreaux par case, quelques fissures."""
    image = Image.new("RGB", (SIZE, SIZE))
    tiles(image, rng, (0, 0, SIZE, SIZE), 16, (176, 180, 172), (92, 94, 90))
    draw = ImageDraw.Draw(image)
    for _ in range(1):  # une fissure discrète
        x, y = rng.randrange(SIZE), rng.randrange(SIZE)
        for _ in range(8):
            nx, ny = x + rng.randint(-3, 3), y + rng.randint(1, 3)
            draw.line((x, y, nx, ny), fill=(118, 120, 114))
            x, y = nx % SIZE, ny % SIZE
    add_stains(image, rng, 3, (60, 52, 40))
    add_noise(image, rng, 6)
    return image


def make_wall(rng: random.Random) -> Image.Image:
    """Faïence verte en bas, peinture beige sale en haut, plinthe sombre au sol."""
    image = Image.new("RGB", (SIZE, WALL_HEIGHT_PIXELS))
    draw = ImageDraw.Draw(image)
    tiles_top = WALL_HEIGHT_PIXELS - 80  # la faïence monte à environ 1,25 m
    draw.rectangle((0, 0, SIZE, tiles_top), fill=(170, 162, 140))  # peinture
    tiles(
        image,
        rng,
        (0, tiles_top, SIZE, WALL_HEIGHT_PIXELS),
        16,
        (120, 150, 130),
        (70, 84, 74),
    )
    draw.rectangle((0, tiles_top - 3, SIZE, tiles_top), fill=(80, 96, 86))  # liseré
    draw.rectangle(
        (0, WALL_HEIGHT_PIXELS - 6, SIZE, WALL_HEIGHT_PIXELS), fill=(48, 46, 42)
    )
    for y in range(tiles_top - 3):  # crasse : plus sombre en haut et près de la faïence
        top_dirt = max(0.0, 0.35 - y / 120)
        low_dirt = max(0.0, 0.25 - (tiles_top - y) / 80)
        for x in range(SIZE):
            pixel = image.getpixel((x, y))
            image.putpixel((x, y), _blend(pixel, (70, 62, 46), top_dirt + low_dirt))
    for _ in range(
        4
    ):  # coulures depuis le plafond, de longueur et d'intensité variables
        x = rng.randrange(SIZE)
        length = rng.randint(15, 80)
        for y in range(length):
            fade = 0.4 * (1 - y / length)
            image.putpixel((x, y), _blend(image.getpixel((x, y)), (80, 70, 50), fade))
    add_stains(image, rng, 3, (70, 62, 48))
    add_noise(image, rng, 5)
    return image


def make_ceiling(rng: random.Random) -> Image.Image:
    """Dalles de faux plafond perforées, 2 x 2 par case, une tachée d'humidité."""
    image = Image.new("RGB", (SIZE, SIZE))
    tiles(image, rng, (0, 0, SIZE, SIZE), 32, (150, 148, 140), (70, 70, 66))
    for x in range(3, SIZE, 4):  # perforations
        for y in range(3, SIZE, 4):
            if x % 32 and y % 32:
                image.putpixel((x, y), (112, 110, 104))
    add_stains(image, rng, 2, (110, 90, 50))
    add_noise(image, rng, 4)
    return image


TEXTURES = {
    "floor_tiles": make_floor,
    "wall_tiles": make_wall,
    "ceiling_tiles": make_ceiling,
}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    for name, make in TEXTURES.items():
        path = OUTPUT / f"{name}.png"
        make(rng).save(path)
        print(f"Texture créée : {path}")


if __name__ == "__main__":
    main()
