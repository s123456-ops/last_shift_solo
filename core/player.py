"""Le joueur : ce qu'il possède. Module indépendant du moteur de jeu."""

from core.flashlight import Flashlight
from core.stamina import Stamina


class Player:
    """Regroupe la lampe et l'endurance du joueur (bientôt son inventaire)."""

    def __init__(self, flashlight: Flashlight, stamina: Stamina) -> None:
        self._flashlight = flashlight
        self._stamina = stamina

    @property
    def flashlight(self) -> Flashlight:
        return self._flashlight

    @property
    def stamina(self) -> Stamina:
        return self._stamina
