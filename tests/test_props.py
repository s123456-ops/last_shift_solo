import pytest

from core.level import load_level, parse_level
from core.props import (
    LENGTHS,
    MapWithFurniture,
    PropFormatError,
    load_props,
    parse_props,
)
from view.props import CATALOG

LEVEL = parse_level("#######\n#PFGE.#\n#.....#\n#..NM.#\n#######")


def test_long_prop_also_takes_the_cell_on_its_right():
    (bed,) = parse_props("2 2 cell_bed N", LEVEL)  # facing north: its right is east
    assert bed.cells == ((2, 2), (2, 3))


def test_right_side_depends_on_facing():
    (bed,) = parse_props("2 3 cell_bed S", LEVEL)  # facing south: its right is west
    assert bed.cells == ((2, 3), (2, 2))


def test_prop_on_an_object_raises():
    with pytest.raises(PropFormatError, match="not free floor"):
        parse_props("1 2 crate N", LEVEL)  # the fuse is at (1, 2)


def test_prop_sticking_into_a_wall_raises():
    with pytest.raises(PropFormatError, match="not free floor"):
        parse_props("2 5 cell_bed N", LEVEL)


def test_two_props_on_the_same_cell_raise():
    with pytest.raises(PropFormatError, match="already taken"):
        parse_props("2 2 crate N\n2 1 cell_bed N", LEVEL)


def test_unknown_prop_raises():
    with pytest.raises(PropFormatError, match="unknown furniture"):
        parse_props("2 2 piano N", LEVEL)


def test_props_block_the_way():
    props = parse_props("2 2 crate N", LEVEL)
    furnished = MapWithFurniture(LEVEL, props)
    assert furnished.is_wall((2, 2))
    assert not furnished.is_wall((2, 3))


def test_every_prop_kind_has_a_look_and_every_look_a_size():
    assert set(CATALOG) == set(LENGTHS)


def test_shipped_props_match_the_shipped_level():
    level = load_level("levels/level1.txt")
    assert load_props("levels/level1_props.txt", level)
