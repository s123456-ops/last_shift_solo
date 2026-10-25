"""Le plan du bâtiment avec ses portes de sécurité. Module indépendant du moteur de jeu."""

from core.interactables import LockedDoor
from core.level import Cell, Obstacles


class MapWithDoors:
    """Le plan vu par le monstre : un mur, ou une porte encore fermée, bloque.

    Il enveloppe le plan d'origine sans le modifier, et les portes restent la seule
    source de vérité : quand le joueur en ouvre une, le monstre peut y passer.
    """

    def __init__(self, level: Obstacles, doors: list[LockedDoor]) -> None:
        self._level = level
        self._doors = {door.cell: door for door in doors}

    def is_wall(self, cell: Cell) -> bool:
        door = self._doors.get(cell)
        if door is not None and door.is_closed:
            return True
        return self._level.is_wall(cell)
