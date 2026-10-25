"""Where to put the traces of abandonment: damaged walls and floor debris.

Everything is drawn at random with a fixed seed: the scenery is identical in
every game, which helps the player find their way. Does not import Ursina:
tested without a window.
"""

import random
from dataclasses import dataclass

from core.level import FLOOR, Cell, FacilityMap

DECOR_SEED = 13
WALL_VARIANTS = (  # (texture, weight): most walls stay intact
    ("wall_tiles", 70),
    ("wall_cracked", 12),
    ("wall_water", 9),
    ("wall_hole", 5),
    ("wall_claws", 4),
)
DEBRIS_DENSITY = 0.10  # share of floor cells that get debris
WALL_DEBRIS = "debris_rubble"  # rubble falls at the foot of walls
FLOOR_DEBRIS = ("debris_papers", "debris_stain", "debris_tiles")
RUBBLE_CHANCE = 0.6  # against a wall, debris is usually rubble
CEILING_HOLE_DENSITY = 0.05  # share of floor cells under a fallen ceiling tile
MAX_CABLES = 2
CABLE_LENGTH = (0.4, 0.9)  # metres: the bottom of the cables stays above head height


@dataclass(frozen=True)
class Debris:
    """A piece of debris lying flat on the floor."""

    cell: Cell
    texture: str
    angle: float  # rotation around the vertical axis, in degrees
    size: float  # side length, in metres
    offset: tuple[float, float]  # offset inside the cell (x, z), to break the alignment


def wall_textures(level: FacilityMap, seed: int = DECOR_SEED) -> dict[Cell, str]:
    """Each wall's texture: normal, cracked, damp, holed or clawed."""
    rng = random.Random(seed)
    names = [name for name, _ in WALL_VARIANTS]
    weights = [weight for _, weight in WALL_VARIANTS]
    return {cell: rng.choices(names, weights)[0] for cell in level.wall_cells()}


def scatter_debris(
    level: FacilityMap, seed: int = DECOR_SEED, density: float = DEBRIS_DENSITY
) -> list[Debris]:
    """Debris on free floor cells (never on an object or a door)."""
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
    """A cable hanging from a hole in the ceiling."""

    offset: tuple[float, float]
    length: float
    tilt: float  # tilt, in degrees


@dataclass(frozen=True)
class CeilingHole:
    """A fallen ceiling tile: a hole above, the broken tile on the floor."""

    cell: Cell
    cables: tuple[Cable, ...]


def ceiling_holes(
    level: FacilityMap, seed: int = DECOR_SEED, density: float = CEILING_HOLE_DENSITY
) -> list[CeilingHole]:
    """The fallen tiles, above free floor cells."""
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
