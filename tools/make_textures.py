"""Génère les textures du bâtiment (style PS1, 64 pixels) dans assets/textures/.

Usage :
    python -m tools.make_textures

Les textures sont dessinées par ce script, pixel par pixel : aucune image
téléchargée, donc aucune licence à créditer. Le hasard est fixé (SEED) :
relancer le script redonne exactement les mêmes images.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

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


# --- Variantes de murs : le bâtiment abandonné depuis six ans -----------------

CRACK = (88, 80, 68)
BRICK = (110, 66, 52)
MORTAR = (96, 90, 80)


def _crack(
    draw: ImageDraw.ImageDraw, rng: random.Random, x: int, y: int, steps: int
) -> None:
    """Une fissure qui descend en zigzag et se divise parfois en deux."""
    for _ in range(steps):
        nx, ny = x + rng.randint(-4, 4), y + rng.randint(2, 6)
        draw.line((x, y, nx, ny), fill=CRACK, width=1)
        if rng.random() < 0.08:
            _crack(draw, rng, nx, ny, steps // 3)
        x, y = max(1, min(SIZE - 2, nx)), ny


def make_wall_cracked(rng: random.Random) -> Image.Image:
    """Le mur, traversé de fissures du plafond jusqu'à la faïence."""
    image = make_wall(rng)
    draw = ImageDraw.Draw(image)
    for _ in range(2):
        _crack(draw, rng, rng.randrange(8, SIZE - 8), rng.randint(0, 40), 16)
    return image


def make_wall_water(rng: random.Random) -> Image.Image:
    """Une infiltration : grande coulure brune et peinture qui cloque."""
    image = make_wall(rng)
    pixels = image.load()
    center = rng.randint(20, SIZE - 20)
    for y in range(image.height - 10):
        spread = 6 + y // 6  # la tache s'élargit en descendant
        for x in range(max(0, center - spread), min(SIZE, center + spread)):
            edge = abs(x - center) / spread
            pixels[x, y] = _blend(
                pixels[x, y], (70, 66, 44), 0.6 * (1 - edge) * (1 - y / image.height)
            )
    for _ in range(6):  # cloques de peinture, à peine plus claires que le mur
        x, y = rng.randrange(SIZE), rng.randrange(10, 100)
        ImageDraw.Draw(image).ellipse((x, y, x + 2, y + 1), fill=(182, 174, 150))
    return image


def make_wall_hole(rng: random.Random) -> Image.Image:
    """Un pan de plâtre arraché, qui laisse voir les briques derrière."""
    image = make_wall(rng)
    bricks = Image.new("RGB", image.size, MORTAR)
    draw = ImageDraw.Draw(bricks)
    for row, y in enumerate(range(0, image.height, 8)):
        offset = 6 if row % 2 else 0
        for x in range(-offset, SIZE, 12):
            draw.rectangle((x + 1, y + 1, x + 11, y + 7), fill=vary(rng, BRICK, 14))
    mask = Image.new("L", image.size, 0)
    shape = ImageDraw.Draw(mask)
    cx, cy = rng.randint(22, SIZE - 22), rng.randint(40, 80)
    points = []
    for step in range(12):  # contour irrégulier du trou
        angle = step / 12 * 6.283
        radius = rng.randint(10, 18)
        points.append(
            (cx + radius * math.cos(angle), cy + radius * 1.4 * math.sin(angle))
        )
    shape.polygon(points, fill=255)
    edge = mask.filter(ImageFilter.MaxFilter(3))
    image.paste(Image.new("RGB", image.size, (60, 56, 50)), (0, 0), edge)  # bord sombre
    image.paste(bricks, (0, 0), mask)
    return image


def make_wall_claws(rng: random.Random) -> Image.Image:
    """Quatre griffures parallèles, à hauteur d'homme. Personne n'en parle."""
    image = make_wall(rng)
    draw = ImageDraw.Draw(image)
    x0, y0 = rng.randint(12, 26), rng.randint(36, 60)
    for claw in range(4):
        x = x0 + claw * 6
        draw.line(
            (x, y0 + claw * 2, x + 22, y0 + 58 + claw * 2), fill=(40, 34, 30), width=2
        )
        draw.line(
            (x + 1, y0 + claw * 2, x + 23, y0 + 58 + claw * 2),
            fill=(150, 140, 120),
            width=1,
        )
    return image


# --- Débris au sol (images avec transparence) ----------------------------------


def _transparent() -> Image.Image:
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def make_rubble(rng: random.Random) -> Image.Image:
    """Des gravats : morceaux de plâtre et de brique, dans un halo de poussière."""
    image = _transparent()
    draw = ImageDraw.Draw(image)
    draw.ellipse((6, 10, SIZE - 6, SIZE - 8), fill=(120, 114, 100, 90))  # poussière
    for _ in range(45):
        x, y = rng.randint(10, SIZE - 14), rng.randint(14, SIZE - 14)
        size = rng.randint(2, 6)
        base = rng.choice([(150, 146, 134), (120, 116, 106), BRICK, (90, 88, 82)])
        draw.rectangle((x, y, x + size, y + size - 1), fill=(*vary(rng, base, 12), 255))
    return image


def make_papers(rng: random.Random) -> Image.Image:
    """Des feuilles éparpillées, jaunies, parfois piétinées."""
    image = _transparent()
    for _ in range(4):
        sheet = Image.new("RGBA", (22, 28), (*vary(rng, (214, 206, 180), 10), 255))
        lines = ImageDraw.Draw(sheet)
        for y in range(5, 25, 3):
            lines.line((3, y, rng.randint(10, 19), y), fill=(110, 106, 96, 255))
        sheet = sheet.rotate(rng.randint(0, 359), expand=True)
        image.alpha_composite(
            sheet, (rng.randint(0, SIZE - 36), rng.randint(0, SIZE - 36))
        )
    return image


def make_stain(rng: random.Random) -> Image.Image:
    """Une tache sombre et irrégulière, d'origine inconnue."""
    image = _transparent()
    pixels = image.load()
    blobs = [
        (rng.randint(20, 44), rng.randint(20, 44), rng.randint(8, 16)) for _ in range(5)
    ]
    for x in range(SIZE):
        for y in range(SIZE):
            strength = max(
                (1 - ((x - bx) ** 2 + (y - by) ** 2) ** 0.5 / r for bx, by, r in blobs),
                default=0,
            )
            if strength > 0:
                pixels[x, y] = (46, 32, 24, int(min(1.0, strength * 1.6) * 170))
    return image


def make_broken_tiles(rng: random.Random) -> Image.Image:
    """Des éclats de carrelage, arrachés du sol."""
    image = _transparent()
    draw = ImageDraw.Draw(image)
    for _ in range(9):
        x, y = rng.randint(6, SIZE - 18), rng.randint(6, SIZE - 18)
        points = [(x + rng.randint(0, 12), y + rng.randint(0, 12)) for _ in range(4)]
        draw.polygon(
            points,
            fill=(*vary(rng, (176, 180, 172), 12), 255),
            outline=(92, 94, 90, 255),
        )
    return image


TEXTURES = {
    "floor_tiles": make_floor,
    "wall_tiles": make_wall,
    "ceiling_tiles": make_ceiling,
    "wall_cracked": make_wall_cracked,
    "wall_water": make_wall_water,
    "wall_hole": make_wall_hole,
    "wall_claws": make_wall_claws,
    "debris_rubble": make_rubble,
    "debris_papers": make_papers,
    "debris_stain": make_stain,
    "debris_tiles": make_broken_tiles,
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
