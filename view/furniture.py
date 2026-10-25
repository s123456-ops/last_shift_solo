"""Mobilier sur lequel reposent les petits objets : bureaux et étagères murales.

Purement décoratif : aucune règle du jeu. Chaque meuble est collé au mur et
n'occupe que ce côté de la case, pour laisser le passage libre.
"""

from dataclasses import dataclass

from ursina import Entity, Vec3, color

from core.level import Cell
from view.coords import cell_to_world
from view.lighting import make_lit

LEG_SIZE = 0.05
BRACKET_SIZE = (0.03, 0.15)  # équerre sous une étagère : épaisseur, hauteur


@dataclass(frozen=True)
class FurnitureStyle:
    """Les dimensions d'un meuble, en mètres (une case = 1 m)."""

    width: float  # le long du mur
    depth: float  # depuis le mur
    top_height: float  # hauteur du plateau au-dessus du sol
    thickness: float
    has_legs: bool  # un bureau a des pieds, une étagère des équerres
    color: object
    solid: bool  # le joueur ne passe pas à travers


DESK = FurnitureStyle(
    width=0.9,
    depth=0.45,
    top_height=0.75,
    thickness=0.05,
    has_legs=True,
    color=color.rgb32(92, 78, 62),
    solid=True,
)
SHELF = FurnitureStyle(
    width=0.8,
    depth=0.25,
    top_height=1.1,
    thickness=0.04,
    has_legs=False,
    color=color.rgb32(110, 112, 108),
    solid=False,  # fixée au mur, au-dessus des hanches : on ne la heurte pas
)


def place_furniture(cell: Cell, wall_side: Cell, style: FurnitureStyle) -> Vec3:
    """Pose le meuble contre le mur et renvoie le centre de son plateau.

    wall_side est la direction (d_ligne, d_colonne) du mur, donnée par
    FacilityMap.wall_side() : c'est le noyau qui sait où sont les murs.
    """
    d_row, d_col = wall_side
    toward_wall = Vec3(d_col, 0, -d_row)  # même convention que cell_to_world
    center = cell_to_world(cell) + toward_wall * (0.5 - style.depth / 2)
    runs_along_x = d_row != 0  # mur au nord ou au sud : le meuble s'allonge en x
    size_x, size_z = (
        (style.width, style.depth) if runs_along_x else (style.depth, style.width)
    )
    _part(
        center,
        (0, style.top_height - style.thickness / 2, 0),
        (size_x, style.thickness, size_z),
        style,
    )
    if style.has_legs:
        _add_legs(center, size_x, size_z, style)
    else:
        _add_brackets(center, size_x, size_z, runs_along_x, style)
    if style.solid:
        Entity(
            model="cube",
            position=center + Vec3(0, style.top_height / 2, 0),
            scale=(size_x, style.top_height, size_z),
            collider="box",
            visible=False,
        )
    return center + Vec3(0, style.top_height, 0)


def _part(center: Vec3, offset: tuple, scale: tuple, style: FurnitureStyle) -> None:
    make_lit(
        Entity(
            model="cube",
            position=center + Vec3(*offset),
            scale=scale,
            color=style.color,
        )
    )


def _add_legs(
    center: Vec3, size_x: float, size_z: float, style: FurnitureStyle
) -> None:
    leg_height = style.top_height - style.thickness
    for side_x in (-1, 1):
        for side_z in (-1, 1):
            offset = (
                side_x * (size_x / 2 - LEG_SIZE),
                leg_height / 2,
                side_z * (size_z / 2 - LEG_SIZE),
            )
            _part(center, offset, (LEG_SIZE, leg_height, LEG_SIZE), style)


def _add_brackets(
    center: Vec3,
    size_x: float,
    size_z: float,
    runs_along_x: bool,
    style: FurnitureStyle,
) -> None:
    thickness, height = BRACKET_SIZE
    y = style.top_height - style.thickness - height / 2
    for side in (-1, 1):
        if runs_along_x:
            offset = (side * (size_x / 2 - 0.1), y, 0)
            scale = (thickness, height, size_z)
        else:
            offset = (0, y, side * (size_z / 2 - 0.1))
            scale = (size_x, height, thickness)
        _part(center, offset, scale, style)
