"""Player settings: each one cycles through its values on every click.

Does not import Ursina: this module is tested without opening a window.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from core.texts import tr

T = TypeVar("T")
Choice = tuple[str, float]  # (key of the displayed text, applied value)

BRIGHTNESS_CHOICES: tuple[Choice, ...] = (  # multiplier of the gloom
    ("brightness.dark", 0.6),
    ("brightness.normal", 1.0),
    ("brightness.bright", 1.8),
    ("brightness.very_bright", 3.0),
)
VOLUME_CHOICES: tuple[Choice, ...] = (  # master volume, from 0 to 1
    ("volume.off", 0.0),
    ("volume.low", 0.35),
    ("volume.medium", 0.7),
    ("volume.high", 1.0),
)
RETRO_CHOICES = (("retro.on", True), ("retro.off", False))  # style PS1
SENSITIVITY_CHOICES: tuple[Choice, ...] = (  # camera speed with the mouse
    ("sensitivity.low", 15),
    ("sensitivity.normal", 25),
    ("sensitivity.high", 40),
    ("sensitivity.very_high", 60),
)


class Setting(Generic[T]):
    """A setting with several values. The view displays it; `apply` puts it into effect.

    The value can be a number (brightness) or an object (difficulty level).
    """

    def __init__(
        self, label_key: str, choices: tuple[tuple[str, T], ...], default: int
    ) -> None:
        if not 0 <= default < len(choices):
            raise ValueError(
                f"Default value {default} is outside the {len(choices)} choices of {label_key}."
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
        """The button text, in the current language ("Volume: high")."""
        return tr(self._label_key, value=tr(self._choices[self._index][0]))

    def bind(self, apply: Callable[[T], None]) -> None:
        """Connects the setting to what it controls, and applies its value right away."""
        self._apply = apply
        apply(self.value)

    def next(self) -> None:
        """Moves to the next value, going back to the start after the last one."""
        self._index = (self._index + 1) % len(self._choices)
        if self._apply is not None:
            self._apply(self.value)


@dataclass(frozen=True)
class PlayerSettings:
    """The settings shared by the title screen and the pause menu."""

    brightness: Setting
    volume: Setting
    sensitivity: Setting
    retro: Setting

    def all(self) -> tuple[Setting, ...]:
        return (self.brightness, self.volume, self.sensitivity, self.retro)


def default_settings() -> PlayerSettings:
    return PlayerSettings(
        brightness=Setting("options.brightness", BRIGHTNESS_CHOICES, default=1),
        volume=Setting("options.volume", VOLUME_CHOICES, default=3),
        sensitivity=Setting("options.sensitivity", SENSITIVITY_CHOICES, default=1),
        retro=Setting("options.retro", RETRO_CHOICES, default=0),
    )
