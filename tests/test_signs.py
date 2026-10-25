import pytest

from core.level import load_level, parse_level
from core.signs import SignFormatError, load_signs, parse_signs
from core.texts import SUPPORTED_LANGUAGES, load_catalog

LEVEL = parse_level("#######\n#PFGE.#\n#..NM.#\n#######")


def test_sign_is_read_with_its_wall_and_direction():
    (sign,) = parse_signs("0 2 S sign.hall", LEVEL)
    assert (sign.wall, sign.facing, sign.key) == ((0, 2), (1, 0), "sign.hall")


def test_comments_and_blank_lines_are_ignored():
    assert parse_signs("# signs\n\n0 2 S sign.hall  # the hall\n", LEVEL)


def test_sign_on_a_floor_cell_raises():
    with pytest.raises(SignFormatError, match="not a wall"):
        parse_signs("1 2 S sign.hall", LEVEL)


def test_sign_facing_another_wall_raises():
    with pytest.raises(SignFormatError, match="another wall"):
        parse_signs("0 2 N sign.hall", LEVEL)


def test_unknown_direction_raises():
    with pytest.raises(SignFormatError, match="unknown direction"):
        parse_signs("0 2 X sign.hall", LEVEL)


def test_incomplete_line_raises():
    with pytest.raises(SignFormatError, match="Line 1"):
        parse_signs("0 2 S", LEVEL)


def test_shipped_signs_match_the_shipped_level_and_are_translated():
    level = load_level("levels/level1.txt")
    signs = load_signs("levels/level1_signs.txt", level)
    assert signs
    for language in SUPPORTED_LANGUAGES:
        catalog = load_catalog(language)
        for sign in signs:
            assert sign.key in catalog, (language, sign.key)
