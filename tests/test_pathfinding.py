from core.level import parse_level
from core.pathfinding import Pathfinder

ROOM = """
#######
#P...F#
#.###.#
#EGNM.#
#######
"""

CLOSED_ROOMS = """
#######
#P#M#F#
#E#G#N#
#######
"""


def _are_adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def test_straight_path():
    pathfinder = Pathfinder(parse_level(ROOM))
    assert pathfinder.find_path((1, 1), (3, 1)) == [(2, 1), (3, 1)]


def test_path_goes_around_walls_and_is_shortest():
    level = parse_level(ROOM)
    path = Pathfinder(level).find_path((1, 3), (3, 3))
    assert len(path) == 6
    assert not any(level.is_wall(cell) for cell in path)


def test_path_is_made_of_adjacent_steps():
    path = Pathfinder(parse_level(ROOM)).find_path((1, 1), (3, 5))
    steps = [(1, 1)] + path
    assert all(_are_adjacent(a, b) for a, b in zip(steps, steps[1:]))


def test_unreachable_goal_returns_empty_path():
    pathfinder = Pathfinder(parse_level(CLOSED_ROOMS))
    assert pathfinder.find_path((1, 1), (1, 3)) == []


def test_already_at_goal_returns_empty_path():
    pathfinder = Pathfinder(parse_level(ROOM))
    assert pathfinder.find_path((1, 1), (1, 1)) == []


def test_next_step_stays_in_place_when_unreachable():
    pathfinder = Pathfinder(parse_level(CLOSED_ROOMS))
    assert pathfinder.next_step((1, 1), (1, 3)) == (1, 1)
