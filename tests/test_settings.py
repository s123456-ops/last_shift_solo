import pytest

from view.settings import Setting, default_settings

CHOICES = (("volume.off", 0.0), ("volume.low", 0.35), ("volume.high", 1.0))


def test_setting_starts_on_its_default_value():
    assert Setting("options.volume", CHOICES, default=1).value == 0.35


def test_next_moves_to_the_following_value():
    setting = Setting("options.volume", CHOICES, default=0)
    setting.next()
    assert setting.value == 0.35


def test_next_wraps_around_after_the_last_value():
    setting = Setting("options.volume", CHOICES, default=2)
    setting.next()
    assert setting.value == 0.0


def test_bind_applies_the_current_value_immediately():
    applied = []
    Setting("options.volume", CHOICES, default=2).bind(applied.append)
    assert applied == [1.0]


def test_each_change_is_applied():
    applied = []
    setting = Setting("options.volume", CHOICES, default=0)
    setting.bind(applied.append)
    setting.next()
    assert applied == [0.0, 0.35]


def test_label_is_translated():
    assert Setting("options.volume", CHOICES, default=2).label == "Volume : fort"


def test_default_outside_the_choices_raises():
    with pytest.raises(ValueError, match="hors des"):
        Setting("options.volume", CHOICES, default=3)


def test_every_default_setting_has_a_label_in_every_language():
    from core.texts import SUPPORTED_LANGUAGES, set_language

    for language in SUPPORTED_LANGUAGES:
        set_language(language)
        for setting in default_settings().all():
            for _ in range(4):  # chaque réglage a 4 valeurs : on les affiche toutes
                assert setting.label
                setting.next()
    set_language("fr")
