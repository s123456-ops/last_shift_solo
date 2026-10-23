"""Le joueur : ce qu'il possède et où il se trouve. Module indépendant du moteur de jeu."""
from core.flashlight import Flashlight
from core.level import Cell
from core.stamina import Stamina


class Player:
    """Regroupe la lampe et l'endurance du joueur, et sait s'il est caché."""

    def __init__(self, flashlight: Flashlight, stamina: Stamina) -> None:
        self._flashlight = flashlight
        self._stamina = stamina
        self._hiding_spot: Cell | None = None

    @property
    def flashlight(self) -> Flashlight:
        return self._flashlight

    @property
    def stamina(self) -> Stamina:
        return self._stamina

    @property
    def is_hidden(self) -> bool:
        return self._hiding_spot is not None

    def hide(self, cell: Cell) -> None:
        """Se cacher éteint la lampe : une lumière dans un casier vous trahirait."""
        self._hiding_spot = cell
        if self._flashlight.is_on:
            self._flashlight.toggle()

    def leave_hiding(self) -> None:
        self._hiding_spot = None