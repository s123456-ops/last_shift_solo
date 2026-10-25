"""Où poser les traces d'abandon : murs abîmés et débris au sol.

Tout est tiré au sort avec une graine fixe : le décor est identique à chaque partie,
ce qui aide le joueur à se repérer. N'importe pas Ursina : se teste sans fenêtre.
"""

import random
from dataclasses import dataclass

from core.level import FLOOR, Cell, FacilityMap

DECOR_SEED = 13
WALL_VARIANTS = (  # (texture, poids) : la plupart des murs restent intacts
    ("wall_tiles", 70),
    ("wall_cracked", 12),
    ("wall_water", 9),
    ("wall_hole", 5),
    ("wall_claws", 4),
)
DEBRIS_DENSITY = 0.10  # part des cases de sol qui reçoivent un débris
WALL_DEBRIS = "debris_rubble"  # les gravats tombent au pied des murs
FLOOR_DEBRIS = ("debris_papers", "debris_stain", "debris_tiles")
RUBBLE_CHANCE = 0.6  # contre un mur, le débris est le plus souvent des gravats
CEILING_HOLE_DENSITY = 0.05  # part des cases de sol sous une dalle tombée
MAX_CABLES = 2
CABLE_LENGTH = (0.4, 0.9)  # mètres : le bas des câbles reste au-dessus des têtes


@dataclass(frozen=True)
class Debris:
    """Un débris posé à plat sur le sol."""

    cell: Cell
    texture: str
    angle: float  # rotation autour de la verticale, en degrés
    size: float  # côté, en mètres
    offset: tuple[
        float, float
    ]  # décalage dans la case (x, z), pour casser l'alignement


def wall_textures(level: FacilityMap, seed: int = DECOR_SEED) -> dict[Cell, str]:
    """La texture de chaque mur : normale, fissurée, humide, trouée ou griffée."""
    rng = random.Random(seed)
    names = [name for name, _ in WALL_VARIANTS]
    weights = [weight for _, weight in WALL_VARIANTS]
    return {cell: rng.choices(names, weights)[0] for cell in level.wall_cells()}


def scatter_debris(
    level: FacilityMap, seed: int = DECOR_SEED, density: float = DEBRIS_DENSITY
) -> list[Debris]:
    """Des débris sur les cases de sol libres (jamais sur un objet ou une porte)."""
    rng = random.Random(seed + 1)
    debris = []
    for row, line in enumerate(level.rows):
        for col, tile in enumerate(line):
            if tile != FLOOR or rng.random() >= density:
                continue
            cell = (row, col)
            against_wall = level.wall_side(cell) is not None
            if against_wall and rng.random() < RUBBLE_CHANCE:
                texture = WALL_DEBRIS
            else:
                texture = rng.choice(FLOOR_DEBRIS)
            debris.append(
                Debris(
                    cell,
                    texture,
                    angle=rng.uniform(0, 360),
                    size=rng.uniform(0.6, 1.0),
                    offset=(rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2)),
                )
            )
    return debris


@dataclass(frozen=True)
class Cable:
    """Un câble qui pend d'un trou du plafond."""

    offset: tuple[float, float]
    length: float
    tilt: float  # inclinaison, en degrés


@dataclass(frozen=True)
class CeilingHole:
    """Une dalle de plafond tombée : un trou en haut, la dalle cassée au sol."""

    cell: Cell
    cables: tuple[Cable, ...]


def ceiling_holes(
    level: FacilityMap, seed: int = DECOR_SEED, density: float = CEILING_HOLE_DENSITY
) -> list[CeilingHole]:
    """Les dalles tombées, au-dessus de cases de sol libres."""
    rng = random.Random(seed + 2)
    holes = []
    for row, line in enumerate(level.rows):
        for col, tile in enumerate(line):
            if tile != FLOOR or rng.random() >= density:
                continue
            cables = tuple(
                Cable(
                    offset=(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3)),
                    length=rng.uniform(*CABLE_LENGTH),
                    tilt=rng.uniform(-12, 12),
                )
                for _ in range(rng.randint(0, MAX_CABLES))
            )
            holes.append(CeilingHole((row, col), cables))
    return holes
