"""Conversion between grid cells (core) and 3D positions (view)."""

from ursina import Vec3

from core.level import Cell


def cell_to_world(cell: Cell, height: float = 0.0) -> Vec3:
    """Cell (row, column) -> 3D position. Row 0 is to the north (z = 0)."""
    row, col = cell
    return Vec3(col, height, -row)


def world_to_grid(position: Vec3) -> tuple[float, float]:
    """3D position -> (row, column) without rounding, for smooth display."""
    return (-position.z, position.x)


def world_to_cell(position: Vec3) -> Cell:
    """3D position -> nearest cell."""
    row, col = world_to_grid(position)
    return (round(row), round(col))
