"""The player: what they own and where they are. Engine-independent module."""

from core.flashlight import Flashlight
from core.inventory import Inventory
from core.level import Cell
from core.stamina import Stamina


class Player:
    """Groups the player's flashlight and stamina, and knows whether they are hidden."""

    def __init__(
        self,
        flashlight: Flashlight,
        stamina: Stamina,
        inventory: Inventory | None = None,
    ) -> None:
        self._flashlight = flashlight
        self._stamina = stamina
        self._inventory = inventory if inventory is not None else Inventory()
        self._hiding_spot: Cell | None = None

    @property
    def inventory(self) -> Inventory:
        return self._inventory

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
        """Hiding switches the flashlight off: a light in a locker would give you away."""
        self._hiding_spot = cell
        if self._flashlight.is_on:
            self._flashlight.toggle()

    def leave_hiding(self) -> None:
        self._hiding_spot = None
