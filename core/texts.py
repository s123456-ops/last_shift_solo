"""Game texts in several languages, stored in locales/<language>.json.

The code only contains keys; this module returns the text in the chosen language.
Engine-independent module.
"""

import json

from core.paths import resource

LOCALES_DIR = resource("locales")
SUPPORTED_LANGUAGES = ("fr", "en")
DEFAULT_LANGUAGE = "en"

_texts: dict[str, str] = {}
_language = ""


def load_catalog(language: str) -> dict[str, str]:
    """Reads a language file, or raises ValueError if the language is not supported."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}' (choices: {', '.join(SUPPORTED_LANGUAGES)})."
        )
    path = LOCALES_DIR / f"{language}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def set_language(language: str) -> None:
    global _texts, _language
    _texts = load_catalog(language)
    _language = language


def current_language() -> str:
    if not _language:
        set_language(DEFAULT_LANGUAGE)
    return _language


def tr(key: str, **values) -> str:
    """The text for the key in the current language, with its values inserted."""
    current_language()  # loads the default language on the first call
    try:
        template = _texts[key]
    except KeyError:
        raise KeyError(f"Missing text for key '{key}' ({_language}).") from None
    return template.format(**values)
