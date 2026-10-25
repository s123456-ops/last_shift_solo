from view.music_mix import MOODS, next_volume


def test_music_gets_quieter_as_the_danger_grows():
    assert MOODS["title"] > MOODS["intro"] > MOODS["game"] > MOODS["chase"] > 0
    assert MOODS["silent"] == 0


def test_fade_moves_step_by_step():
    volume = next_volume(0.55, 0.1, dt=1.0)
    assert 0.1 < volume < 0.55


def test_fade_never_overshoots():
    assert next_volume(0.12, 0.1, dt=1.0) == 0.1
    assert next_volume(0.0, 0.4, dt=10.0) == 0.4


def test_fade_from_title_to_game_takes_under_two_seconds():
    volume, seconds = MOODS["title"], 0.0
    while volume != MOODS["game"]:
        volume = next_volume(volume, MOODS["game"], dt=1 / 60)
        seconds += 1 / 60
    assert seconds < 2
