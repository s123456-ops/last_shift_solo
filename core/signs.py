"""Signs fixed to walls: loading and validating their placement.

File format: one line per sign,
    row column direction key
where (row, column) is a wall, direction (N, S, E, W) the side the sign is
screwed on, and key the text to display (in locales/). # starts a comment.

Engine-independent module.
"""

from dataclasses import dataclass
from pathlib import Path

from core.level import Cell, FacilityMap

DIRECTIONS = {"N": (-1, 0), "S": (1, 0), "W": (0, -1), "E": (0, 1)}


class SignFormatError(ValueError):
    """The signs file is malformed or does not match the map."""


@dataclass(frozen=True)
class Sign:
    """A sign screwed on a wall face, facing a room or a corridor."""

    wall: Cell
    facing: Cell  # direction (d_row, d_col) it faces
    key: str  # text key, for example "sign.archives"


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
            f"Line {number}: expected 'row column direction key', got '{line}'."
        )
    row_text, col_text, direction, key = parts
    if not (row_text.isdigit() and col_text.isdigit()):
        raise SignFormatError(f"Line {number}: the position must be two numbers.")
    if direction not in DIRECTIONS:
        raise SignFormatError(
            f"Line {number}: unknown direction '{direction}' (N, S, E or W)."
        )
    wall = (int(row_text), int(col_text))
    facing = DIRECTIONS[direction]
    if not level.is_wall(wall):
        raise SignFormatError(f"Line {number}: cell {wall} is not a wall.")
    front = (wall[0] + facing[0], wall[1] + facing[1])
    if level.is_wall(front):
        raise SignFormatError(f"Line {number}: the sign on {wall} faces another wall.")
    return Sign(wall, facing, key)
