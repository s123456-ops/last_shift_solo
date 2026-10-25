"""Room furniture: beds, shelves, crates... and the cells it occupies.

File format: one line per piece of furniture,
    row column kind direction
where (row, column) is the first occupied cell, and direction (N, S, E, W)
the side the furniture faces. Long furniture also takes the cells
on its right. # starts a comment.

The core does not know what furniture looks like (that is the view's job), only
the space it takes: the player and the monster must walk around it.

Engine-independent module.
"""

from dataclasses import dataclass
from pathlib import Path

from core.level import FLOOR, Cell, FacilityMap, Obstacles
from core.signs import DIRECTIONS

LENGTHS = {  # number of occupied cells, from left to right
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
    """The furniture file is malformed or does not match the map."""


@dataclass(frozen=True)
class Prop:
    """A piece of furniture placed on the map."""

    anchor: Cell
    kind: str
    facing: Cell  # direction (d_row, d_col) it faces

    @property
    def right(self) -> Cell:
        """The furniture's right side, seen from the front: east, for furniture facing north."""
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
    """The map where furniture blocks the way, for the player and the monster alike."""

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
                    f"Line {number}: '{prop.kind}' spills over cell {cell}, "
                    "which is not free floor."
                )
            if cell in taken:
                raise PropFormatError(
                    f"Line {number}: cell {cell} is already taken by another piece of furniture."
                )
            taken.add(cell)
        props.append(prop)
    return props


def _parse_line(line: str, number: int) -> Prop:
    parts = line.split()
    if len(parts) != 4:
        raise PropFormatError(
            f"Line {number}: expected 'row column kind direction', got '{line}'."
        )
    row_text, col_text, kind, direction = parts
    if not (row_text.isdigit() and col_text.isdigit()):
        raise PropFormatError(f"Line {number}: the position must be two numbers.")
    if kind not in LENGTHS:
        raise PropFormatError(f"Line {number}: unknown furniture '{kind}'.")
    if direction not in DIRECTIONS:
        raise PropFormatError(
            f"Line {number}: unknown direction '{direction}' (N, S, E or W)."
        )
    return Prop((int(row_text), int(col_text)), kind, DIRECTIONS[direction])
