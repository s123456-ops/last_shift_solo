from core.level import parse_level
from core.perception import can_hear, can_see

LEVEL = parse_level("""
#########
#.......#
#P..#..M#
#.......#
#EFG..N.#
#########
""")


def test_wall_blocks_sight():
    assert not can_see(LEVEL, (2, 7), (2, 1), max_distance=10)


def test_clear_line_allows_sight():
    assert can_see(LEVEL, (2, 7), (1, 2), max_distance=10)


def test_target_too_far_is_not_seen():
    assert not can_see(LEVEL, (2, 7), (1, 2), max_distance=4)


def test_hearing_goes_through_walls():
    assert can_hear((2, 7), (2, 1), max_distance=6)


def test_target_too_far_is_not_heard():
    assert not can_hear((2, 7), (2, 1), max_distance=5)
