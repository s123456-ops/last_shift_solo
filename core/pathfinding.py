"""Recherche du plus court chemin sur la grille du niveau (parcours en largeur).

Module indépendant du moteur de jeu.
"""
from collections import deque
from collections.abc import Iterator

from core.level import Cell, FacilityMap

DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))  # haut, bas, gauche, droite


class Pathfinder:
    """Calcule des chemins entre deux cases sans traverser les murs."""

    def __init__(self, level: FacilityMap) -> None:
        self._level = level

    def find_path(self, start: Cell, goal: Cell) -> list[Cell]:
        """Renvoie les cases à parcourir de start à goal (start exclu, goal inclus).

        Liste vide si goal est inaccessible ou si on y est déjà.
        """
        if self._level.is_wall(start) or self._level.is_wall(goal):
            return []
        came_from: dict[Cell, Cell | None] = {start: None}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            if current == goal:
                return self._rebuild_path(came_from, goal)
            for neighbour in self._walkable_neighbours(current):
                if neighbour not in came_from:
                    came_from[neighbour] = current
                    queue.append(neighbour)
        return []

    def next_step(self, start: Cell, goal: Cell) -> Cell:
        """Prochaine case vers goal, ou start si aucun chemin n'existe."""
        path = self.find_path(start, goal)
        return path[0] if path else start

    def _walkable_neighbours(self, cell: Cell) -> Iterator[Cell]:
        row, col = cell
        for d_row, d_col in DIRECTIONS:
            neighbour = (row + d_row, col + d_col)
            if not self._level.is_wall(neighbour):
                yield neighbour

    @staticmethod
    def _rebuild_path(came_from: dict[Cell, Cell | None], goal: Cell) -> list[Cell]:
        path = []
        cell = goal
        while came_from[cell] is not None:
            path.append(cell)
            cell = came_from[cell]
        path.reverse()
        return path