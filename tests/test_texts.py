import re

import pytest

from core.texts import SUPPORTED_LANGUAGES, load_catalog, set_language, tr

PLACEHOLDER = re.compile(r"\{(\w+)\}")


@pytest.fixture(autouse=True)
def restore_french():
    yield
    set_language("fr")  # les autres tests comparent des textes français


def test_every_language_has_the_same_keys():
    reference = load_catalog("fr").keys()
    for language in SUPPORTED_LANGUAGES:
        assert load_catalog(language).keys() == reference, language


def test_translations_keep_the_same_placeholders():
    french = load_catalog("fr")
    for language in SUPPORTED_LANGUAGES:
        for key, text in load_catalog(language).items():
            assert set(PLACEHOLDER.findall(text)) == set(
                PLACEHOLDER.findall(french[key])
            ), key


def test_switching_to_english():
    set_language("en")
    assert tr("title.start") == "Start"


def test_values_are_inserted():
    set_language("en")
    assert tr("note.prompt", title="Memo") == "Read: Memo"


def test_unknown_language_raises():
    with pytest.raises(ValueError):
        set_language("xx")


def test_missing_key_raises_a_clear_error():
    with pytest.raises(KeyError, match="nope"):
        tr("nope")
