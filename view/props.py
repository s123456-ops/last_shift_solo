"""À quoi ressemble chaque meuble : une liste de blocs, comme sur PS1.

Repère d'un meuble : x vers sa droite, y vers le haut, z vers l'avant (le côté
où il regarde). L'origine est le centre de sa première case, au sol. Un meuble
de 2 cases s'étend jusqu'à x = 1. Un meuble « contre le mur » a son dos en z = -0.5.

N'importe pas Ursina : ce sont des données, vérifiées par les tests.
"""

from dataclasses import dataclass

Color = tuple[int, int, int]
Vector = tuple[float, float, float]

DARK_METAL = (70, 72, 76)
STEEL = (150, 154, 158)
RUST = (118, 82, 60)
WOOD = (110, 82, 56)
CARDBOARD = (150, 120, 80)
PORCELAIN = (200, 198, 188)
MATTRESS = (168, 162, 144)
SHEET = (182, 188, 190)
FABRIC = (64, 68, 78)
LAB_GREEN = (70, 108, 104)
BLACK = (24, 24, 28)
MURKY_GREEN = (70, 120, 90)
CRT = (176, 172, 156)
SCREEN = (22, 40, 30)
RED = (140, 36, 32)
OLIVE = (108, 114, 100)


@dataclass(frozen=True)
class Part:
    """Un bloc du meuble : centre, taille (en mètres) et couleur."""

    center: Vector
    size: Vector
    color: Color


def _legs(
    x_range: tuple[float, float],
    z_range: tuple[float, float],
    height: float,
    color: Color,
) -> list[Part]:
    """Quatre pieds fins aux coins d'un plateau."""
    return [
        Part((x, height / 2, z), (0.05, height, 0.05), color)
        for x in x_range
        for z in z_range
    ]


def _rack(z: float) -> list[Part]:
    """Une étagère métallique de 2 cases, chargée de cartons."""
    parts = [
        Part((x, 1.0, z + dz), (0.05, 2.0, 0.05), DARK_METAL)
        for x in (-0.45, 1.45)
        for dz in (-0.2, 0.2)
    ]
    shelves = (0.1, 0.55, 1.0, 1.45, 1.9)
    parts += [Part((0.5, y, z), (1.95, 0.03, 0.45), STEEL) for y in shelves]
    boxes = (  # (étagère, position x) : rangées irrégulières, comme un vrai dépôt
        (0, -0.25),
        (0, 0.2),
        (0, 1.15),
        (1, -0.2),
        (1, 0.6),
        (1, 1.0),
        (1, 1.3),
        (2, 0.1),
        (2, 0.9),
        (3, -0.25),
        (3, 0.2),
        (3, 0.65),
        (3, 1.25),
    )
    parts += [
        Part((x, shelves[shelf] + 0.17, z), (0.36, 0.3, 0.38), CARDBOARD)
        for shelf, x in boxes
    ]
    return parts


def _bed(top: float, frame_color: Color, cover: Color, headboard: bool) -> list[Part]:
    parts = [
        Part((0.5, top - 0.07, -0.07), (1.9, 0.1, 0.85), frame_color),
        Part((0.5, top + 0.05, -0.07), (1.85, 0.14, 0.8), cover),
        Part((-0.2, top + 0.15, -0.07), (0.4, 0.07, 0.6), PORCELAIN),  # oreiller
    ]
    parts += _legs((-0.42, 1.42), (-0.45, 0.31), top - 0.12, frame_color)
    if headboard:
        parts.append(Part((-0.45, top + 0.2, -0.07), (0.05, 0.6, 0.85), frame_color))
    return parts


def _desk(with_monitors: bool) -> list[Part]:
    parts = [
        Part((0.5, 0.75, -0.15), (1.4, 0.05, 0.7), WOOD),
        Part((-0.17, 0.36, -0.15), (0.05, 0.72, 0.66), WOOD),
        Part((1.0, 0.36, -0.15), (0.4, 0.72, 0.66), WOOD),  # caisson à tiroirs
        Part((0.4, 0.45, 0.28), (0.45, 0.06, 0.45), FABRIC),  # assise de la chaise
        Part((0.4, 0.22, 0.28), (0.05, 0.42, 0.05), DARK_METAL),
        Part((0.4, 0.75, 0.48), (0.45, 0.5, 0.06), FABRIC),  # dossier
    ]
    if with_monitors:
        for x in (0.15, 0.75):
            parts.append(Part((x, 0.95, -0.25), (0.4, 0.35, 0.4), CRT))
            parts.append(Part((x, 0.96, -0.045), (0.32, 0.25, 0.01), SCREEN))
        parts.append(Part((0.45, 0.79, 0.05), (0.45, 0.03, 0.15), CRT))  # clavier
    else:
        parts.append(Part((0.15, 0.78, -0.2), (0.3, 0.01, 0.22), PORCELAIN))  # papiers
    return parts


def _crate(size: float, y: float, x: float = 0.0) -> list[Part]:
    return [
        Part((x, y, 0), (size, size, size), WOOD),
        Part((x, y, size / 2 + 0.005), (size * 0.9, 0.06, 0.01), RUST),  # latte
    ]


CATALOG: dict[str, list[Part]] = {
    "archive_rack": _rack(z=0.0),
    "wall_rack": _rack(z=-0.27),
    "bench": [
        Part((0.5, 0.45, 0), (1.9, 0.05, 0.35), WOOD),
        Part((-0.35, 0.21, 0), (0.05, 0.42, 0.3), DARK_METAL),
        Part((1.35, 0.21, 0), (0.05, 0.42, 0.3), DARK_METAL),
    ],
    "break_table": [
        Part((0, 0.74, 0), (0.9, 0.04, 0.9), (170, 170, 160)),
        Part((0, 0.36, 0), (0.08, 0.72, 0.08), DARK_METAL),
        Part((0, 0.015, 0), (0.5, 0.03, 0.5), DARK_METAL),
    ],
    "chair": [
        Part((0, 0.45, 0), (0.42, 0.05, 0.42), FABRIC),
        Part((0, 0.7, -0.19), (0.42, 0.45, 0.04), FABRIC),
        *_legs((-0.18, 0.18), (-0.18, 0.18), 0.43, DARK_METAL),
    ],
    "cell_bed": _bed(top=0.45, frame_color=DARK_METAL, cover=MATTRESS, headboard=False),
    "hospital_bed": _bed(top=0.65, frame_color=STEEL, cover=SHEET, headboard=True),
    "gurney": [
        Part((0.5, 0.8, 0), (1.9, 0.08, 0.6), STEEL),
        Part((0.5, 0.88, 0), (1.85, 0.08, 0.55), SHEET),
        Part((1.4, 0.9, 0.25), (0.03, 1.8, 0.03), STEEL),  # pied à perfusion
        *_legs((-0.4, 1.4), (-0.25, 0.25), 0.76, STEEL),
    ],
    "crate": _crate(0.9, 0.45),
    "crate_stack": [*_crate(0.9, 0.45), *_crate(0.65, 1.23, x=0.08)],
    "filing_cabinet": [
        Part((0, 0.65, -0.2), (0.5, 1.3, 0.6), OLIVE),
        *[Part((0, y, 0.105), (0.44, 0.02, 0.01), BLACK) for y in (0.33, 0.65, 0.97)],
        *[Part((0, y, 0.11), (0.12, 0.03, 0.02), STEEL) for y in (0.5, 0.82, 1.14)],
    ],
    "guard_desk": _desk(with_monitors=True),
    "office_desk": _desk(with_monitors=False),
    "lab_bench": [
        Part((0.5, 0.425, -0.15), (1.9, 0.85, 0.7), LAB_GREEN),
        Part((0.5, 0.875, -0.15), (1.95, 0.05, 0.75), BLACK),
        *[
            Part((x, 1.0, -0.3), (0.08, 0.2, 0.08), color)
            for x, color in (
                (-0.2, MURKY_GREEN),
                (0.0, RUST),
                (0.15, MURKY_GREEN),
                (1.1, RUST),
            )
        ],
        Part((0.7, 1.05, -0.3), (0.2, 0.3, 0.25), DARK_METAL),  # microscope
    ],
    "sink": [
        Part((0, 0.8, -0.3), (0.5, 0.18, 0.4), PORCELAIN),
        Part((0, 0.36, -0.42), (0.06, 0.72, 0.06), DARK_METAL),
        Part((0, 1.5, -0.49), (0.45, 0.55, 0.02), (150, 160, 158)),  # miroir terni
    ],
    "specimen_tank": [
        Part((0, 0.15, 0), (0.8, 0.3, 0.8), DARK_METAL),
        Part((0, 1.1, 0), (0.68, 1.6, 0.68), MURKY_GREEN),  # liquide trouble
        Part((0, 1.97, 0), (0.8, 0.14, 0.8), DARK_METAL),
        Part((0.3, 2.5, 0.3), (0.06, 1.0, 0.06), DARK_METAL),  # tuyau vers le plafond
    ],
    "toilet": [
        Part((0, 0.2, -0.2), (0.4, 0.4, 0.5), STEEL),
        Part((0, 0.42, -0.2), (0.42, 0.04, 0.52), DARK_METAL),
        Part((0, 0.62, -0.41), (0.45, 0.4, 0.18), STEEL),
    ],
    "vending_machine": [
        Part((0, 0.9, -0.15), (0.9, 1.8, 0.7), RED),
        Part((-0.1, 1.1, 0.205), (0.55, 1.1, 0.02), (40, 50, 60)),  # vitre
        Part((0.3, 0.4, 0.205), (0.2, 0.15, 0.02), BLACK),
    ],
    "workbench": [
        Part((0.5, 0.88, -0.15), (1.9, 0.06, 0.7), WOOD),
        *_legs((-0.4, 1.4), (-0.45, 0.15), 0.85, DARK_METAL),
        Part((0.2, 0.99, -0.25), (0.45, 0.16, 0.22), RED),  # caisse à outils
    ],
}
