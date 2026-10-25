"""Difficulty levels: each one is a settings object, not a chain of conditions.

Engine-independent module.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Difficulty:
    """Everything that changes between easy, normal and hard."""

    name_key: str  # key of the displayed text ("easy")
    grace_period: float  # seconds before the monster starts moving
    monster_patrol_speed: float  # cells per second
    monster_chase_speed: float
    monster_hearing: float  # hearing range, in cells
    flashlight_drain: float  # battery lost per second (out of 100)
    plan_shows_keycard: bool  # a hint for beginners
    plan_shows_player: bool  # without "You are here", players must find their own way
    monster_opens_doors: bool = False  # otherwise, a closed door stops it

    def __post_init__(self) -> None:
        numbers = (
            self.grace_period,
            self.monster_patrol_speed,
            self.monster_chase_speed,
            self.monster_hearing,
            self.flashlight_drain,
        )
        if any(number <= 0 for number in numbers):
            raise ValueError(f"{self.name_key}: every setting must be positive.")
        if self.monster_chase_speed < self.monster_patrol_speed:
            raise ValueError(
                f"{self.name_key}: the monster must chase faster than it patrols."
            )


EASY = Difficulty(
    name_key="difficulty.easy",
    grace_period=40,
    monster_patrol_speed=1.5,
    monster_chase_speed=3,
    monster_hearing=4,
    flashlight_drain=1.25,  # 80 seconds of light
    plan_shows_keycard=True,
    plan_shows_player=True,
)
NORMAL = Difficulty(
    name_key="difficulty.normal",
    grace_period=20,
    monster_patrol_speed=2,
    monster_chase_speed=4,
    monster_hearing=6,
    flashlight_drain=2,  # 50 seconds of light
    plan_shows_keycard=False,
    plan_shows_player=True,
)
HARD = Difficulty(
    name_key="difficulty.hard",
    grace_period=10,
    monster_patrol_speed=2.5,
    monster_chase_speed=5,
    monster_hearing=8,
    flashlight_drain=100 / 35,  # 35 seconds of light
    plan_shows_keycard=False,
    plan_shows_player=False,
    monster_opens_doors=True,
)
DIFFICULTIES = (EASY, NORMAL, HARD)
