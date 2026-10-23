"""Objets avec lesquels le joueur interagit (touche E).

Module indépendant du moteur de jeu.
"""

from abc import ABC, abstractmethod

from core.level import Cell
from core.player import Player

REACH = (
    (0, 0),
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
)  # la case du joueur et ses 4 voisines


class Interactable(ABC):
    """Un objet posé sur une case. Chaque sous-classe définit son effet."""

    def __init__(self, cell: Cell) -> None:
        self._cell = cell
        self._consumed = False

    @property
    def cell(self) -> Cell:
        return self._cell

    @property
    def is_consumed(self) -> bool:
        """Vrai quand l'objet a été utilisé et doit disparaître."""
        return self._consumed

    @property
    @abstractmethod
    def prompt(self) -> str:
        """Texte affiché quand le joueur est à portée."""

    @abstractmethod
    def interact(self, player: Player) -> str:
        """Applique l'effet de l'objet et renvoie le message à afficher."""


class BatteryPickup(Interactable):
    """Une pile qui recharge la lampe, utilisable une seule fois."""

    def __init__(self, cell: Cell, charge: float = 40) -> None:
        super().__init__(cell)
        self._charge = charge

    @property
    def prompt(self) -> str:
        return "Ramasser la pile"

    def interact(self, player: Player) -> str:
        player.flashlight.recharge(self._charge)
        self._consumed = True
        return "Pile insérée dans la lampe."


class Interactions:
    """Les objets du niveau, retrouvés par leur case."""

    def __init__(self, items: list[Interactable]) -> None:
        self._items: dict[Cell, Interactable] = {}
        for item in items:
            if item.cell in self._items:
                raise ValueError(f"Deux objets sur la case {item.cell}.")
            self._items[item.cell] = item

    def near(self, cell: Cell) -> Interactable | None:
        """L'objet encore disponible sur la case du joueur ou une case voisine."""
        row, col = cell
        for d_row, d_col in REACH:
            item = self._items.get((row + d_row, col + d_col))
            if item is not None and not item.is_consumed:
                return item
        return None
