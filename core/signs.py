"""Panneaux fixés aux murs : chargement et validation de leur emplacement.

Format du fichier : une ligne par panneau,
    ligne colonne direction clé
où (ligne, colonne) est un mur, direction (N, S, E, O) le côté où le panneau
est vissé, et clé le texte à afficher (dans locales/). # commence un commentaire.

Module indépendant du moteur de jeu.
"""

from dataclasses import dataclass
from pathlib import Path

from core.level import Cell, FacilityMap

DIRECTIONS = {"N": (-1, 0), "S": (1, 0), "O": (0, -1), "E": (0, 1)}


class SignFormatError(ValueError):
    """Le fichier des panneaux est mal formé ou ne correspond pas à la carte."""


@dataclass(frozen=True)
class Sign:
    """Un panneau vissé sur une face de mur, tourné vers une pièce ou un couloir."""

    wall: Cell
    facing: Cell  # direction (d_ligne, d_colonne) vers laquelle il regarde
    key: str  # clé du texte, par exemple « sign.archives »


def load_signs(path: str | Path, level: FacilityMap) -> list[Sign]:
    return parse_signs(Path(path).read_text(encoding="utf-8"), level)


def parse_signs(text: str, level: FacilityMap) -> list[Sign]:
    signs = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if line:
            signs.append(_parse_line(line, number, level))
    return signs


def _parse_line(line: str, number: int, level: FacilityMap) -> Sign:
    parts = line.split()
    if len(parts) != 4:
        raise SignFormatError(
            f"Ligne {number} : il faut « ligne colonne direction clé », reçu « {line} »."
        )
    row_text, col_text, direction, key = parts
    if not (row_text.isdigit() and col_text.isdigit()):
        raise SignFormatError(f"Ligne {number} : la position doit être deux nombres.")
    if direction not in DIRECTIONS:
        raise SignFormatError(
            f"Ligne {number} : direction « {direction} » inconnue (N, S, E ou O)."
        )
    wall = (int(row_text), int(col_text))
    facing = DIRECTIONS[direction]
    if not level.is_wall(wall):
        raise SignFormatError(f"Ligne {number} : la case {wall} n'est pas un mur.")
    front = (wall[0] + facing[0], wall[1] + facing[1])
    if level.is_wall(front):
        raise SignFormatError(
            f"Ligne {number} : le panneau en {wall} regarde vers un autre mur."
        )
    return Sign(wall, facing, key)
