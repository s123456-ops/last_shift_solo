"""Image du plan du bâtiment, dessinée case par case à partir de la carte.

N'importe pas Ursina : ce module se teste sans ouvrir de fenêtre.
"""

from dataclasses import dataclass

from PIL import Image

from core.level import Cell, FacilityMap

WALL_RGB = (170, 170, 160)
FLOOR_RGB = (28, 28, 32)
EXIT_RGB = (70, 200, 100)
PANEL_RGB = (80, 150, 255)
FUSE_RGB = (240, 200, 60)
DOOR_RGB = (170, 100, 45)
KEYCARD_RGB = (60, 210, 230)


@dataclass(frozen=True)
class Landmark:
    """Un lieu repéré sur le plan, avec sa légende et sa couleur."""

    cell: Cell
    label_key: str
    rgb: tuple[int, int, int]


def landmarks(level: FacilityMap, show_keycard: bool = False) -> list[Landmark]:
    """Les lieux utiles au joueur. Les piles n'y sont jamais ; la carte, en indice."""
    marks = [
        Landmark(level.exit_cell, "map.exit", EXIT_RGB),
        Landmark(level.power_panel_cell, "map.panel", PANEL_RGB),
        Landmark(level.fuse_cell, "map.fuse", FUSE_RGB),
    ]
    marks += [
        Landmark(cell, "map.door", DOOR_RGB) for cell in level.security_door_cells
    ]
    if show_keycard and level.keycard_cell is not None:
        marks.append(Landmark(level.keycard_cell, "map.keycard", KEYCARD_RGB))
    return marks


def draw_plan(level: FacilityMap) -> Image.Image:
    """Un pixel par case : les murs en clair, le sol en sombre."""
    image = Image.new("RGBA", (level.width, level.height), (*FLOOR_RGB, 255))
    for row, col in level.wall_cells():
        image.putpixel((col, row), (*WALL_RGB, 255))  # (x, y) = (colonne, ligne)
    return image
