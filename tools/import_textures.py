"""Prépare les textures des objets à partir des images de assets/textures/source/.

Usage :
    python -m tools.import_textures

Pour chaque image : on retire le fond uni autour de l'objet, puis on réduit
à la résolution d'un jeu PS1. Les originaux restent intacts dans source/.
"""

from pathlib import Path

from PIL import Image, ImageChops

TEXTURES = Path(__file__).resolve().parent.parent / "assets" / "textures"
SOURCE = TEXTURES / "source"
BACKGROUND_TOLERANCE = 24  # écart de couleur au-delà duquel un pixel n'est plus le fond
MARGIN = 2  # pixels gardés autour de l'objet, pour ne pas rogner ses bords

# nom de l'image source → (nom de la texture du jeu, taille finale en pixels)
OBJECT_TEXTURES = {
    "door": ("door", (64, 144)),
    "security_door": ("security_door", (64, 144)),
    "locker": ("locker", (64, 160)),
    "document": ("document", (64, 80)),
    "note": ("note", (64, 72)),
    "keycard": ("keycard", (64, 48)),
    "battery": ("battery", (32, 64)),
    "fuse": ("fuse", (64, 32)),
}


def crop_to_object(image: Image.Image) -> Image.Image:
    """Recadre sur l'objet : le fond est la couleur du coin en haut à gauche."""
    background = Image.new("RGB", image.size, image.getpixel((0, 0)))
    difference = ImageChops.difference(image, background).convert("L")
    mask = difference.point(lambda value: 255 if value > BACKGROUND_TOLERANCE else 0)
    box = mask.getbbox()
    if box is None:
        raise ValueError("Aucun objet trouvé : l'image n'est faite que de fond.")
    left, top, right, bottom = box
    return image.crop(
        (
            max(0, left - MARGIN),
            max(0, top - MARGIN),
            min(image.width, right + MARGIN),
            min(image.height, bottom + MARGIN),
        )
    )


def prepare(source: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(source).convert("RGB")
    return crop_to_object(image).resize(size, Image.BOX)  # BOX : moyenne, sans flou


def main() -> None:
    for source_name, (texture_name, size) in OBJECT_TEXTURES.items():
        matches = sorted(SOURCE.glob(f"{source_name}.*"))
        if not matches:
            print(f"Image manquante, ignorée : {source_name}")
            continue
        destination = TEXTURES / f"{texture_name}.png"
        prepare(matches[0], size).save(destination)
        print(f"Texture créée : {destination.name} {size}")


if __name__ == "__main__":
    main()
