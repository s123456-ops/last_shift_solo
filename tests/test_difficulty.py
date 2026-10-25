import pytest

from core.difficulty import DIFFICULTIES, EASY, HARD, NORMAL, Difficulty
from core.texts import SUPPORTED_LANGUAGES, load_catalog


def test_normal_is_the_original_game():
    assert NORMAL.grace_period == 20
    assert (NORMAL.monster_patrol_speed, NORMAL.monster_chase_speed) == (2, 4)
    assert NORMAL.monster_hearing == 6
    assert NORMAL.flashlight_drain == 2


@pytest.mark.parametrize(("easier", "harder"), [(EASY, NORMAL), (NORMAL, HARD)])
def test_each_level_is_harder_than_the_previous_one(easier, harder):
    assert harder.grace_period < easier.grace_period
    assert harder.monster_chase_speed > easier.monster_chase_speed
    assert harder.monster_hearing > easier.monster_hearing
    assert harder.flashlight_drain > easier.flashlight_drain


def test_only_easy_shows_the_keycard_on_the_plan():
    assert [level.plan_shows_keycard for level in DIFFICULTIES] == [True, False, False]


def test_hard_hides_the_player_on_the_plan():
    assert not HARD.plan_shows_player


def test_monster_slower_in_chase_than_in_patrol_raises():
    with pytest.raises(ValueError, match="plus vite"):
        Difficulty("test", 20, 4, 2, 6, 2, False, True)


def test_negative_setting_raises():
    with pytest.raises(ValueError, match="positifs"):
        Difficulty("test", -5, 2, 4, 6, 2, False, True)


def test_every_difficulty_has_a_name_in_every_language():
    for language in SUPPORTED_LANGUAGES:
        catalog = load_catalog(language)
        for level in DIFFICULTIES:
            assert level.name_key in catalog, (language, level.name_key)
