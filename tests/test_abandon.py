from core.level import FLOOR, load_level, parse_level
from view.abandon import WALL_DEBRIS, WALL_VARIANTS, scatter_debris, wall_textures

LEVEL = load_level("levels/level1.txt")


def test_decor_is_the_same_every_game():
    assert scatter_debris(LEVEL) == scatter_debris(LEVEL)
    assert wall_textures(LEVEL) == wall_textures(LEVEL)


def test_another_seed_gives_another_decor():
    assert scatter_debris(LEVEL, seed=1) != scatter_debris(LEVEL, seed=2)


def test_debris_lie_only_on_free_floor():
    for debris in scatter_debris(LEVEL):
        row, col = debris.cell
        assert LEVEL.rows[row][col] == FLOOR, debris.cell


def test_rubble_falls_only_next_to_a_wall():
    for debris in scatter_debris(LEVEL):
        if debris.texture == WALL_DEBRIS:
            assert LEVEL.wall_side(debris.cell) is not None, debris.cell


def test_density_stays_reasonable():
    floor_cells = sum(line.count(FLOOR) for line in LEVEL.rows)
    count = len(scatter_debris(LEVEL))
    assert 0.05 * floor_cells < count < 0.15 * floor_cells


def test_every_wall_gets_a_known_texture():
    known = {name for name, _ in WALL_VARIANTS}
    textures = wall_textures(LEVEL)
    assert set(textures) == set(LEVEL.wall_cells())
    assert set(textures.values()) <= known


def test_no_debris_when_density_is_zero():
    level = parse_level("#####\n#PFE#\n#GNM#\n#####")
    assert scatter_debris(level, density=0) == []
