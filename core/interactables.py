"""Objets avec lesquels le joueur interagit (touche E).

Module indépendant du moteur de jeu.
"""

from abc import ABC, abstractmethod

from core.facility import Facility
from core.inventory import FUSE_ITEM, PANEL_CODE
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


class HidingSpot(Interactable):
    """Un casier où se cacher. Il n'est jamais consommé : on peut y revenir."""

    def __init__(self, cell: Cell) -> None:
        super().__init__(cell)
        self._occupied = False

    @property
    def prompt(self) -> str:
        return "Sortir du casier" if self._occupied else "Se cacher dans le casier"

    def interact(self, player: Player) -> str:
        if self._occupied:
            self._occupied = False
            player.leave_hiding()
            return "Vous sortez du casier."
        self._occupied = True
        player.hide(self.cell)
        return "Vous retenez votre souffle..."


class Pickup(Interactable):
    """Un objet à ramasser, qui rejoint l'inventaire (le fusible)."""

    def __init__(self, cell: Cell, item: str, prompt: str, message: str) -> None:
        super().__init__(cell)
        self._item = item
        self._prompt = prompt
        self._message = message

    @property
    def prompt(self) -> str:
        return self._prompt

    def interact(self, player: Player) -> str:
        player.inventory.add(self._item)
        self._consumed = True
        return self._message


class Note(Interactable):
    """Un texte à lire, qui peut apprendre quelque chose au joueur (le code)."""

    def __init__(
        self, cell: Cell, title: str, text: str, grants: str | None = None
    ) -> None:
        super().__init__(cell)
        self._title = title
        self._text = text
        self._grants = grants

    @property
    def prompt(self) -> str:
        return f"Lire : {self._title}"

    def interact(self, player: Player) -> str:
        if self._grants is not None:
            player.inventory.add(self._grants)
        return f"{self._title}\n\n{self._text}"


class PowerPanel(Interactable):
    """Le tableau électrique : fusible + code = courant rétabli."""

    def __init__(self, cell: Cell, facility: Facility) -> None:
        super().__init__(cell)
        self._facility = facility

    @property
    def prompt(self) -> str:
        return "Examiner le tableau électrique"

    def interact(self, player: Player) -> str:
        if self._facility.power_on:
            return "Le courant est rétabli."
        if not player.inventory.has(FUSE_ITEM):
            return "Un fusible a grillé. Il en faut un de rechange."
        if not player.inventory.has(PANEL_CODE):
            return "Le tableau demande un code à trois chiffres."
        player.inventory.remove(FUSE_ITEM)
        self._facility.restore_power()
        return "Le courant revient. La sortie est déverrouillée !"


class ExitDoor(Interactable):
    """La porte de sortie, verrouillée tant que le courant n'est pas rétabli."""

    def __init__(self, cell: Cell, facility: Facility) -> None:
        super().__init__(cell)
        self._facility = facility

    @property
    def prompt(self) -> str:
        return "Ouvrir la porte de sortie"

    def interact(self, player: Player) -> str:
        if not self._facility.power_on:
            return "Verrouillée. Sans courant, la porte ne s'ouvrira pas."
        self._facility.reach_exit()
        return "05 h 58. Vous rendez votre badge."


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
