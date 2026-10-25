"""Chargement et validation des niveaux.

Ce module ne dépend d'aucun moteur de jeu : il peut être testé sans ouvrir de fenêtre.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

WALL = "#"
FLOOR = "."
PLAYER_START = "P"
MONSTER_START = "M"
EXIT = "E"
FUSE = "F"
POWER_PANEL = "G"
NOTE = "N"
BATTERY = "B"
DOCUMENT = "D"
EMERGENCY_LIGHT = "L"
HIDING_SPOT = "H"
KEYCARD = "K"
SECURITY_DOOR = "S"
KNOWN_TILES = {
    WALL,
    FLOOR,
    PLAYER_START,
    MONSTER_START,
    EXIT,
    FUSE,
    POWER_PANEL,
    NOTE,
    BATTERY,
    DOCUMENT,
    EMERGENCY_LIGHT,
    HIDING_SPOT,
    KEYCARD,
    SECURITY_DOOR,
}


Cell = tuple[int, int]  # (ligne, colonne)


class Obstacles(Protocol):
    """Tout ce qui sait dire si une case bloque le passage et la vue.

    FacilityMap en fait partie, mais aussi MapWithDoors (core/doors.py) :
    le monstre et la recherche de chemin acceptent l'un comme l'autre.
    """

    def is_wall(self, cell: Cell) -> bool: ...


class LevelFormatError(ValueError):
    """Le contenu du niveau ne respecte pas le format attendu."""


@dataclass(frozen=True)
class FacilityMap:
    """Plan du bâtiment : une grille de cases et la position des éléments du jeu."""

    rows: tuple[str, ...]
    player_start: Cell
    monster_start: Cell
    exit_cell: Cell
    fuse_cell: Cell
    power_panel_cell: Cell
    note_cell: Cell
    battery_cells: tuple[Cell, ...]
    document_cells: tuple[Cell, ...]
    emergency_light_cells: tuple[Cell, ...]
    hiding_spot_cells: tuple[Cell, ...]
    keycard_cell: Cell | None = None  # facultative : un niveau peut s'en passer
    security_door_cells: tuple[Cell, ...] = ()

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return len(self.rows[0])

    def is_wall(self, cell: Cell) -> bool:
        """Une case hors de la carte est considérée comme un mur."""
        row, col = cell
        if not (0 <= row < self.height and 0 <= col < self.width):
            return True
        return self.rows[row][col] == WALL

    def wall_cells(self) -> list[Cell]:
        return _cells_with(self.rows, WALL)


def load_level(path: str | Path) -> FacilityMap:
    """Lit un fichier de niveau et le valide."""
    text = Path(path).read_text(encoding="utf-8")
    return parse_level(text)


def parse_level(text: str) -> FacilityMap:
    """Transforme le texte d'un niveau en FacilityMap, ou lève LevelFormatError."""
    rows = [line.rstrip() for line in text.strip().splitlines()]
    if not rows or not rows[0]:
        raise LevelFormatError("Le niveau est vide.")
    _check_rectangular(rows)
    _check_known_tiles(rows)
    keycard_cell = _find_optional(rows, KEYCARD)
    security_door_cells = tuple(_cells_with(rows, SECURITY_DOOR))
    if security_door_cells and keycard_cell is None:
        raise LevelFormatError(
            f"Le niveau contient une porte de sécurité '{SECURITY_DOOR}' "
            f"mais aucune carte d'accès '{KEYCARD}' : la partie serait impossible."
        )
    return FacilityMap(
        rows=tuple(rows),
        player_start=_find_unique(rows, PLAYER_START),
        monster_start=_find_unique(rows, MONSTER_START),
        exit_cell=_find_unique(rows, EXIT),
        fuse_cell=_find_unique(rows, FUSE),
        power_panel_cell=_find_unique(rows, POWER_PANEL),
        note_cell=_find_unique(rows, NOTE),
        battery_cells=tuple(_cells_with(rows, BATTERY)),
        document_cells=tuple(_cells_with(rows, DOCUMENT)),
        emergency_light_cells=tuple(_cells_with(rows, EMERGENCY_LIGHT)),
        hiding_spot_cells=tuple(_cells_with(rows, HIDING_SPOT)),
        keycard_cell=keycard_cell,
        security_door_cells=security_door_cells,
    )


def _cells_with(rows, tile: str) -> list[Cell]:
    return [
        (row, col)
        for row, line in enumerate(rows)
        for col, char in enumerate(line)
        if char == tile
    ]


def _check_rectangular(rows: list[str]) -> None:
    expected = len(rows[0])
    for number, line in enumerate(rows, start=1):
        if len(line) != expected:
            raise LevelFormatError(
                f"La ligne {number} fait {len(line)} caractères au lieu de {expected}."
            )


def _check_known_tiles(rows: list[str]) -> None:
    for number, line in enumerate(rows, start=1):
        for col, char in enumerate(line, start=1):
            if char not in KNOWN_TILES:
                raise LevelFormatError(
                    f"Caractère inconnu '{char}' ligne {number}, colonne {col}."
                )


def _find_unique(rows: list[str], tile: str) -> Cell:
    found = _cells_with(rows, tile)
    if len(found) != 1:
        raise LevelFormatError(
            f"Le niveau doit contenir exactement un '{tile}' (trouvé : {len(found)})."
        )
    return found[0]


def _find_optional(rows: list[str], tile: str) -> Cell | None:
    """La case du symbole s'il est présent une fois, None s'il est absent."""
    found = _cells_with(rows, tile)
    if len(found) > 1:
        raise LevelFormatError(
            f"Le niveau contient au plus un '{tile}' (trouvé : {len(found)})."
        )
    return found[0] if found else None
