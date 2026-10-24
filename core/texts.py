"""Textes du jeu en plusieurs langues, rangés dans locales/<langue>.json.

Le code ne contient que des clés ; ce module renvoie le texte dans la langue choisie.
Module indépendant du moteur de jeu.
"""

import json
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
SUPPORTED_LANGUAGES = ("fr", "en")
DEFAULT_LANGUAGE = "fr"

_texts: dict[str, str] = {}
_language = ""


def load_catalog(language: str) -> dict[str, str]:
    """Lit le fichier d'une langue, ou lève ValueError si elle n'est pas prise en charge."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Langue « {language} » non prise en charge (choix : {', '.join(SUPPORTED_LANGUAGES)})."
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
    """Le texte de la clé dans la langue courante, avec ses valeurs insérées."""
    current_language()  # charge la langue par défaut au premier appel
    try:
        template = _texts[key]
    except KeyError:
        raise KeyError(f"Texte manquant pour la clé « {key} » ({_language}).") from None
    return template.format(**values)
