"""The building plan with its security doors. Engine-independent module."""

from collections.abc import Sequence
from typing import Protocol

from core.level import Cell, Obstacles


class Barrier(Protocol):
    """Anything that can block a cell: a security door or a regular door."""

    @property
    def cell(self) -> Cell: ...

    @property
    def is_closed(self) -> bool: ...


class MapWithDoors:
    """The map as the monster sees it: a wall, or a door still closed, blocks the way.

    It wraps the original map without changing it, and the doors remain the single
    source of truth: when the player opens one, the monster can go through.
    """

    def __init__(self, level: Obstacles, doors: Sequence[Barrier]) -> None:
        self._level = level
        self._doors = {door.cell: door for door in doors}

    def is_wall(self, cell: Cell) -> bool:
        door = self._doors.get(cell)
        if door is not None and door.is_closed:
            return True
        return self._level.is_wall(cell)
