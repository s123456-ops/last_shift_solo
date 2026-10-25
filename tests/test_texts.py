import re

import pytest

from core.texts import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    load_catalog,
    set_language,
    tr,
)

PLACEHOLDER = re.compile(r"\{(\w+)\}")


@pytest.fixture(autouse=True)
def restore_default_language():
    yield
    set_language(DEFAULT_LANGUAGE)  # the other tests compare English texts


def test_every_language_has_the_same_keys():
    reference = load_catalog(DEFAULT_LANGUAGE).keys()
    for language in SUPPORTED_LANGUAGES:
        assert load_catalog(language).keys() == reference, language


def test_translations_keep_the_same_placeholders():
    reference = load_catalog(DEFAULT_LANGUAGE)
    for language in SUPPORTED_LANGUAGES:
        for key, text in load_catalog(language).items():
            assert set(PLACEHOLDER.findall(text)) == set(
                PLACEHOLDER.findall(reference[key])
            ), key


def test_switching_to_english():
    set_language("en")
    assert tr("title.quit") == "Quit"


def test_values_are_inserted():
    set_language("en")
    assert tr("note.prompt", title="Memo") == "Read: Memo"


def test_unknown_language_raises():
    with pytest.raises(ValueError):
        set_language("xx")


def test_missing_key_raises_a_clear_error():
    with pytest.raises(KeyError, match="nope"):
        tr("nope")


def test_every_language_names_itself_for_the_title_screen():
    names = set()
    for language in SUPPORTED_LANGUAGES:
        set_language(language)
        names.add(tr("language.name"))
    assert len(names) == len(SUPPORTED_LANGUAGES)  # two languages, two names
