from core.level import parse_level
from core.texts import SUPPORTED_LANGUAGES, load_catalog
from view.plan_image import FLOOR_RGB, WALL_RGB, draw_plan, landmarks

LEVEL = parse_level("""
#######
#PFGE.#
#K.NSM#
#######
""")


def test_plan_has_one_pixel_per_cell():
    assert draw_plan(LEVEL).size == (LEVEL.width, LEVEL.height)


def test_walls_and_floor_have_their_colors():
    image = draw_plan(LEVEL)
    assert image.getpixel((0, 0))[:3] == WALL_RGB
    assert image.getpixel((1, 1))[:3] == FLOOR_RGB  # (x, y) = (column, row)


def test_landmarks_point_to_the_key_places():
    places = {mark.label_key: mark.cell for mark in landmarks(LEVEL)}
    assert places["map.exit"] == LEVEL.exit_cell
    assert places["map.panel"] == LEVEL.power_panel_cell
    assert places["map.fuse"] == LEVEL.fuse_cell
    assert places["map.door"] == (2, 4)


def test_hidden_items_are_not_on_the_plan():
    cells = {mark.cell for mark in landmarks(LEVEL)}
    assert LEVEL.keycard_cell not in cells


def test_every_landmark_has_a_label_in_every_language():
    for language in SUPPORTED_LANGUAGES:
        catalog = load_catalog(language)
        for mark in landmarks(LEVEL):
            assert mark.label_key in catalog, (language, mark.label_key)


def test_keycard_can_be_shown_as_a_hint():
    cells = {mark.cell for mark in landmarks(LEVEL, show_keycard=True)}
    assert LEVEL.keycard_cell in cells


def test_keycard_hint_has_a_label_in_every_language():
    for language in SUPPORTED_LANGUAGES:
        assert "map.keycard" in load_catalog(language), language
