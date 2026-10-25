import pytest

from core.level import LevelFormatError, load_level, parse_level

SMALL_LEVEL = """
#######
#P.F.E#
#.#.#M#
#G.BN.#
#######
"""


def test_parse_finds_special_cells():
    level = parse_level(SMALL_LEVEL)
    assert level.player_start == (1, 1)
    assert level.monster_start == (2, 5)
    assert level.exit_cell == (1, 5)
    assert level.fuse_cell == (1, 3)
    assert level.power_panel_cell == (3, 1)
    assert level.note_cell == (3, 4)
    assert level.battery_cells == ((3, 3),)
    assert (level.width, level.height) == (7, 5)


def test_walls_and_outside_of_map_are_blocking():
    level = parse_level(SMALL_LEVEL)
    assert level.is_wall((0, 0))
    assert level.is_wall((2, 2))
    assert not level.is_wall((1, 2))
    assert not level.is_wall((1, 3))  # un objet n'est pas un mur
    assert level.is_wall((-1, 0))
    assert level.is_wall((10, 10))


def test_empty_level_raises():
    with pytest.raises(LevelFormatError):
        parse_level("   \n   ")


def test_non_rectangular_level_raises():
    with pytest.raises(LevelFormatError, match="ligne 2"):
        parse_level("#####\n#P.E\n#.#M#\n#####")


def test_unknown_tile_raises():
    with pytest.raises(LevelFormatError, match="X"):
        parse_level("#####\n#PXE#\n#..M#\n#####")


def test_missing_player_raises():
    with pytest.raises(LevelFormatError, match="'P'"):
        parse_level("#####\n#..E#\n#..M#\n#####")


def test_two_players_raise():
    with pytest.raises(LevelFormatError, match="'P'"):
        parse_level("#####\n#PPE#\n#..M#\n#####")


def test_shipped_level_is_valid():
    level = load_level("levels/level1.txt")
    assert not level.is_wall(level.player_start)


"""dernier test vérifie que le vrai niveau du jeu est valide. Si un coéquipier casse la carte un jour, les tests le signaleront avant même de lancer le jeu."""


def test_missing_fuse_raises():
    with pytest.raises(LevelFormatError, match="'F'"):
        parse_level("#####\n#P.E#\n#.GM#\n#..N#\n#####")


def test_level_without_battery_is_valid():
    level = parse_level("######\n#PFGE#\n#..NM#\n######")
    assert level.battery_cells == ()


def test_several_batteries_are_found():
    level = parse_level("######\n#PFGE#\n#BBNM#\n######")
    assert level.battery_cells == ((2, 1), (2, 2))


def test_document_cells_are_found():
    level = parse_level("######\n#PFGE#\n#DDNM#\n######")
    assert level.document_cells == ((2, 1), (2, 2))


def test_level_without_document_is_valid():
    level = parse_level("######\n#PFGE#\n#..NM#\n######")
    assert level.document_cells == ()


def test_emergency_light_cells_are_found():
    level = parse_level("######\n#PFGE#\n#LLNM#\n######")
    assert level.emergency_light_cells == ((2, 1), (2, 2))


def test_level_without_emergency_light_is_valid():
    level = parse_level("######\n#PFGE#\n#..NM#\n######")
    assert level.emergency_light_cells == ()


def test_hiding_spot_cells_are_found():
    level = parse_level("######\n#PFGE#\n#HHNM#\n######")
    assert level.hiding_spot_cells == ((2, 1), (2, 2))


def test_keycard_and_security_doors_are_found():
    level = parse_level("#######\n#PFGE.#\n#K.NSM#\n#######")
    assert level.keycard_cell == (2, 1)
    assert level.security_door_cells == ((2, 4),)


def test_level_without_keycard_or_door_is_valid():
    level = parse_level(SMALL_LEVEL)
    assert level.keycard_cell is None
    assert level.security_door_cells == ()


def test_security_door_cell_is_not_a_wall_on_the_map():
    level = parse_level("#######\n#PFGE.#\n#K.NSM#\n#######")
    assert not level.is_wall((2, 4))  # c'est MapWithDoors qui la ferme


def test_door_without_keycard_raises():
    with pytest.raises(LevelFormatError, match="carte d'accès"):
        parse_level("#######\n#PFGE.#\n#..NSM#\n#######")


def test_two_keycards_raise():
    with pytest.raises(LevelFormatError, match="'K'"):
        parse_level("#######\n#PFGE.#\n#KKN.M#\n#######")


def test_wall_side_finds_the_wall_next_to_a_cell():
    level = parse_level(SMALL_LEVEL)
    assert level.wall_side((1, 1)) == (-1, 0)  # le mur du nord passe en premier


def test_wall_side_ignores_an_isolated_bit_of_wall():
    level = parse_level("#######\n#P...E#\n#..#..#\n#F.G.N#\n#..M..#\n#######")
    assert level.wall_side((2, 2)) is None  # (2, 3) est un pan de mur isolé


def test_wall_side_is_none_in_the_middle_of_a_room():
    level = parse_level("#######\n#P....#\n#..F..#\n#G.N.E#\n#..M..#\n#######")
    assert level.wall_side((2, 3)) is None
