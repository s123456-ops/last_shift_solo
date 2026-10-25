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


def test_small_items_rest_against_a_straight_wall():
    """Piles, notes et documents sont posés sur un meuble collé au mur."""
    small_items = [
        LEVEL.fuse_cell,
        LEVEL.note_cell,
        LEVEL.keycard_cell,
        *LEVEL.battery_cells,
        *LEVEL.document_cells,
    ]
    for cell in small_items:
        assert LEVEL.wall_side(cell) is not None, cell


def test_exit_door_stands_against_a_wall():
    assert LEVEL.wall_side(LEVEL.exit_cell) is not None
