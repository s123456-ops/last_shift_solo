"""Conversion entre les cases de la grille (noyau) et les positions 3D (vue)."""

from ursina import Vec3

from core.level import Cell


def cell_to_world(cell: Cell, height: float = 0.0) -> Vec3:
    """Case (ligne, colonne) → position 3D. La ligne 0 est au nord (z = 0)."""
    row, col = cell
    return Vec3(col, height, -row)


def world_to_cell(position: Vec3) -> Cell:
    """Position 3D → case la plus proche."""
    return (round(-position.z), round(position.x))
