"""Vérifie que le vrai niveau du jeu est jouable de bout en bout."""

from core.doors import MapWithDoors
from core.interactables import LockedDoor
from core.level import load_level
from core.pathfinding import Pathfinder

LEVEL = load_level("levels/level1.txt")


def test_every_object_is_reachable_once_the_doors_are_open():
    pathfinder = Pathfinder(LEVEL)  # sur le plan brut, les portes sont du sol
    targets = [
        LEVEL.exit_cell,
        LEVEL.fuse_cell,
        LEVEL.power_panel_cell,
        LEVEL.note_cell,
        *LEVEL.battery_cells,
        *LEVEL.document_cells,
        *LEVEL.hiding_spot_cells,
    ]
    for cell in targets:
        assert pathfinder.find_path(LEVEL.player_start, cell), cell


def test_keycard_is_reachable_without_opening_any_door():
    doors = [LockedDoor(cell) for cell in LEVEL.security_door_cells]
    pathfinder = Pathfinder(MapWithDoors(LEVEL, doors))
    assert pathfinder.find_path(LEVEL.player_start, LEVEL.keycard_cell)