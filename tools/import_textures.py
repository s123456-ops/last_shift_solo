"""Prepares the object textures from the images in assets/textures/source/.

Usage:
    python -m tools.import_textures

For each image: the plain background around the object is removed, then the
image is shrunk to the resolution of a PS1 game. Originals stay untouched in source/.
"""

from pathlib import Path

from PIL import Image, ImageChops

TEXTURES = Path(__file__).resolve().parent.parent / "assets" / "textures"
SOURCE = TEXTURES / "source"
BACKGROUND_TOLERANCE = (
    24  # colour difference beyond which a pixel is no longer background
)
MARGIN = 2  # pixels kept around the object, so its edges are not cut

# source image name -> (game texture name, final size in pixels)
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
    """Crops to the object: the background is the colour of the top-left corner."""
    background = Image.new("RGB", image.size, image.getpixel((0, 0)))
    difference = ImageChops.difference(image, background).convert("L")
    mask = difference.point(lambda value: 255 if value > BACKGROUND_TOLERANCE else 0)
    box = mask.getbbox()
    if box is None:
        raise ValueError("No object found: the image is only background.")
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
    return crop_to_object(image).resize(size, Image.BOX)  # BOX: average, no blur


def main() -> None:
    for source_name, (texture_name, size) in OBJECT_TEXTURES.items():
        matches = sorted(SOURCE.glob(f"{source_name}.*"))
        if not matches:
            print(f"Missing image, skipped: {source_name}")
            continue
        destination = TEXTURES / f"{texture_name}.png"
        prepare(matches[0], size).save(destination)
        print(f"Texture created: {destination.name} {size}")


if __name__ == "__main__":
    main()
