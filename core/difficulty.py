"""Niveaux de difficulté : chacun est un objet de réglages, pas une suite de conditions.

Module indépendant du moteur de jeu.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Difficulty:
    """Tout ce qui change entre facile, normal et difficile."""

    name_key: str  # clé du texte affiché (« facile »)
    grace_period: float  # secondes avant que le monstre ne bouge
    monster_patrol_speed: float  # cases par seconde
    monster_chase_speed: float
    monster_hearing: float  # portée de l'ouïe, en cases
    flashlight_drain: float  # batterie perdue par seconde (sur 100)
    plan_shows_keycard: bool  # un indice pour les débutants
    plan_shows_player: bool  # sans « Vous êtes ici », il faut se repérer seul
    monster_opens_doors: bool = False  # sinon, une porte fermée l'arrête

    def __post_init__(self) -> None:
        numbers = (
            self.grace_period,
            self.monster_patrol_speed,
            self.monster_chase_speed,
            self.monster_hearing,
            self.flashlight_drain,
        )
        if any(number <= 0 for number in numbers):
            raise ValueError(
                f"{self.name_key} : tous les réglages doivent être positifs."
            )
        if self.monster_chase_speed < self.monster_patrol_speed:
            raise ValueError(
                f"{self.name_key} : le monstre doit courir plus vite qu'il ne rôde."
            )


EASY = Difficulty(
    name_key="difficulty.easy",
    grace_period=40,
    monster_patrol_speed=1.5,
    monster_chase_speed=3,
    monster_hearing=4,
    flashlight_drain=1.25,  # 80 secondes d'éclairage
    plan_shows_keycard=True,
    plan_shows_player=True,
)
NORMAL = Difficulty(
    name_key="difficulty.normal",
    grace_period=20,
    monster_patrol_speed=2,
    monster_chase_speed=4,
    monster_hearing=6,
    flashlight_drain=2,  # 50 secondes d'éclairage
    plan_shows_keycard=False,
    plan_shows_player=True,
)
HARD = Difficulty(
    name_key="difficulty.hard",
    grace_period=10,
    monster_patrol_speed=2.5,
    monster_chase_speed=5,
    monster_hearing=8,
    flashlight_drain=100 / 35,  # 35 secondes d'éclairage
    plan_shows_keycard=False,
    plan_shows_player=False,
    monster_opens_doors=True,
)
DIFFICULTIES = (EASY, NORMAL, HARD)
