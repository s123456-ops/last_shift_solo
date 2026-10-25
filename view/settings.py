"""Réglages du joueur : chacun fait défiler ses valeurs à chaque clic.

N'importe pas Ursina : ce module se teste sans ouvrir de fenêtre.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from core.texts import tr

T = TypeVar("T")
Choice = tuple[str, float]  # (clé du texte affiché, valeur appliquée)

BRIGHTNESS_CHOICES: tuple[Choice, ...] = (  # multiplicateur de la pénombre
    ("brightness.dark", 0.6),
    ("brightness.normal", 1.0),
    ("brightness.bright", 1.8),
    ("brightness.very_bright", 3.0),
)
VOLUME_CHOICES: tuple[Choice, ...] = (  # volume général, de 0 à 1
    ("volume.off", 0.0),
    ("volume.low", 0.35),
    ("volume.medium", 0.7),
    ("volume.high", 1.0),
)
SENSITIVITY_CHOICES: tuple[Choice, ...] = (  # vitesse de la caméra à la souris
    ("sensitivity.low", 15),
    ("sensitivity.normal", 25),
    ("sensitivity.high", 40),
    ("sensitivity.very_high", 60),
)


class Setting(Generic[T]):
    """Un réglage à plusieurs valeurs. La vue l'affiche ; `apply` le met en œuvre.

    La valeur peut être un nombre (luminosité) ou un objet (niveau de difficulté).
    """

    def __init__(
        self, label_key: str, choices: tuple[tuple[str, T], ...], default: int
    ) -> None:
        if not 0 <= default < len(choices):
            raise ValueError(
                f"Valeur par défaut {default} hors des {len(choices)} choix de {label_key}."
            )
        self._label_key = label_key
        self._choices = choices
        self._index = default
        self._apply: Callable[[T], None] | None = None

    @property
    def value(self) -> T:
        return self._choices[self._index][1]

    @property
    def label(self) -> str:
        """Le texte du bouton, dans la langue courante (« Volume : fort »)."""
        return tr(self._label_key, value=tr(self._choices[self._index][0]))

    def bind(self, apply: Callable[[T], None]) -> None:
        """Branche le réglage sur ce qu'il pilote, et applique tout de suite sa valeur."""
        self._apply = apply
        apply(self.value)

    def next(self) -> None:
        """Passe à la valeur suivante, en revenant au début après la dernière."""
        self._index = (self._index + 1) % len(self._choices)
        if self._apply is not None:
            self._apply(self.value)


@dataclass(frozen=True)
class PlayerSettings:
    """Les réglages partagés par l'écran titre et le menu pause."""

    brightness: Setting
    volume: Setting
    sensitivity: Setting

    def all(self) -> tuple[Setting, ...]:
        return (self.brightness, self.volume, self.sensitivity)


def default_settings() -> PlayerSettings:
    return PlayerSettings(
        brightness=Setting("options.brightness", BRIGHTNESS_CHOICES, default=1),
        volume=Setting("options.volume", VOLUME_CHOICES, default=3),
        sensitivity=Setting("options.sensitivity", SENSITIVITY_CHOICES, default=1),
    )
