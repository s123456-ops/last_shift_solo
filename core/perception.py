"""Perception du monstre : vue et ouïe sur la grille.

Module indépendant du moteur de jeu.
"""

import math

from core.level import Cell, Obstacles


def distance(a: Cell, b: Cell) -> float:
    return math.dist(a, b)


def cells_between(a: Cell, b: Cell) -> list[Cell]:
    """Cases traversées par la ligne droite entre a et b, extrémités exclues."""
    steps = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
    cells = []
    for i in range(1, steps):
        t = i / steps
        cells.append((round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t)))
    return cells


def can_see(
    level: Obstacles, observer: Cell, target: Cell, max_distance: float
) -> bool:
    """Vrai si la cible est assez proche et qu'aucun mur ne coupe la ligne de vue."""
    if distance(observer, target) > max_distance:
        return False
    return not any(level.is_wall(cell) for cell in cells_between(observer, target))


def can_hear(observer: Cell, target: Cell, max_distance: float) -> bool:
    """L'ouïe traverse les murs : seule la distance compte."""
    return distance(observer, target) <= max_distance
