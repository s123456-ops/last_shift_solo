"""Le mobilier des pièces : lits, étagères, caisses… et les cases qu'il occupe.

Format du fichier : une ligne par meuble,
    ligne colonne type direction
où (ligne, colonne) est la première case occupée, et direction (N, S, E, O)
le côté vers lequel le meuble est tourné. Un meuble long occupe aussi les
cases à sa droite. # commence un commentaire.

Le noyau ne sait pas à quoi ressemblent les meubles (c'est la vue), seulement
la place qu'ils prennent : le joueur et le monstre doivent en faire le tour.

Module indépendant du moteur de jeu.
"""

from dataclasses import dataclass
from pathlib import Path

from core.level import FLOOR, Cell, FacilityMap, Obstacles
from core.signs import DIRECTIONS

LENGTHS = {  # nombre de cases occupées, de gauche à droite
    "archive_rack": 2,
    "bench": 2,
    "break_table": 1,
    "cell_bed": 2,
    "chair": 1,
    "crate": 1,
    "crate_stack": 1,
    "filing_cabinet": 1,
    "guard_desk": 2,
    "gurney": 2,
    "hospital_bed": 2,
    "lab_bench": 2,
    "office_desk": 2,
    "sink": 1,
    "specimen_tank": 1,
    "toilet": 1,
    "vending_machine": 1,
    "wall_rack": 2,
    "workbench": 2,
}


class PropFormatError(ValueError):
    """Le fichier du mobilier est mal formé ou ne correspond pas à la carte."""


@dataclass(frozen=True)
class Prop:
    """Un meuble posé sur la carte."""

    anchor: Cell
    kind: str
    facing: Cell  # direction (d_ligne, d_colonne) vers laquelle il est tourné

    @property
    def right(self) -> Cell:
        """La droite du meuble, vue de face : pour un meuble tourné au nord, l'est."""
        d_row, d_col = self.facing
        return (d_col, -d_row)

    @property
    def cells(self) -> tuple[Cell, ...]:
        row, col = self.anchor
        r_row, r_col = self.right
        return tuple(
            (row + i * r_row, col + i * r_col) for i in range(LENGTHS[self.kind])
        )


class MapWithFurniture:
    """La carte où les meubles bloquent le passage, pour le joueur comme le monstre."""

    def __init__(self, level: Obstacles, props: list[Prop] | tuple[Prop, ...]) -> None:
        self._level = level
        self._blocked = {cell for prop in props for cell in prop.cells}

    def is_wall(self, cell: Cell) -> bool:
        return cell in self._blocked or self._level.is_wall(cell)


def load_props(path: str | Path, level: FacilityMap) -> list[Prop]:
    return parse_props(Path(path).read_text(encoding="utf-8"), level)


def parse_props(text: str, level: FacilityMap) -> list[Prop]:
    props: list[Prop] = []
    taken: set[Cell] = set()
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        prop = _parse_line(line, number)
        for cell in prop.cells:
            row, col = cell
            inside = 0 <= row < level.height and 0 <= col < level.width
            if not inside or level.rows[row][col] != FLOOR:
                raise PropFormatError(
                    f"Ligne {number} : « {prop.kind} » déborde sur la case {cell}, "
                    "qui n'est pas du sol libre."
                )
            if cell in taken:
                raise PropFormatError(
                    f"Ligne {number} : la case {cell} est déjà prise par un autre meuble."
                )
            taken.add(cell)
        props.append(prop)
    return props


def _parse_line(line: str, number: int) -> Prop:
    parts = line.split()
    if len(parts) != 4:
        raise PropFormatError(
            f"Ligne {number} : il faut « ligne colonne type direction », reçu « {line} »."
        )
    row_text, col_text, kind, direction = parts
    if not (row_text.isdigit() and col_text.isdigit()):
        raise PropFormatError(f"Ligne {number} : la position doit être deux nombres.")
    if kind not in LENGTHS:
        raise PropFormatError(f"Ligne {number} : meuble « {kind} » inconnu.")
    if direction not in DIRECTIONS:
        raise PropFormatError(
            f"Ligne {number} : direction « {direction} » inconnue (N, S, E ou O)."
        )
    return Prop((int(row_text), int(col_text)), kind, DIRECTIONS[direction])
