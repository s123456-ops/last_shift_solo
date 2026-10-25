"""Objets avec lesquels le joueur interagit (touche E).

Module indépendant du moteur de jeu.
"""

from abc import ABC, abstractmethod

from core.facility import Facility
from core.inventory import CODE_END, CODE_START, FUSE_ITEM, KEYCARD_ITEM
from core.level import Cell
from core.player import Player
from core.texts import tr

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
    def is_readable(self) -> bool:
        """Vrai si l'interaction ouvre un texte à lire, affiché en grand."""
        return False

    def reachable_from(self, cell: Cell) -> bool:
        """Le joueur, sur cette case, peut-il utiliser l'objet ? Oui, par défaut."""
        return True

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
        return tr("battery.prompt")

    def interact(self, player: Player) -> str:
        player.flashlight.recharge(self._charge)
        self._consumed = True
        return tr("battery.message")


class HidingSpot(Interactable):
    """Un casier où se cacher. Il n'est jamais consommé : on peut y revenir."""

    def __init__(self, cell: Cell) -> None:
        super().__init__(cell)
        self._occupied = False

    @property
    def prompt(self) -> str:
        return (
            tr("locker.prompt_leave") if self._occupied else tr("locker.prompt_enter")
        )

    def interact(self, player: Player) -> str:
        if self._occupied:
            self._occupied = False
            player.leave_hiding()
            return tr("locker.leave")
        self._occupied = True
        player.hide(self.cell)
        return tr("locker.enter")


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
        return tr("note.prompt", title=self._title)

    @property
    def is_readable(self) -> bool:
        return True

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
        return tr("panel.prompt")

    def interact(self, player: Player) -> str:
        if self._facility.power_on:
            return tr("panel.powered")
        if not player.inventory.has(FUSE_ITEM):
            return tr("panel.no_fuse")
        if not player.inventory.has(CODE_START):
            return tr("panel.no_code")
        if not player.inventory.has(CODE_START):
            return tr("panel.no_code")
        if not player.inventory.has(CODE_END):
            return tr("panel.code_incomplete")
        player.inventory.remove(FUSE_ITEM)
        self._facility.restore_power()
        return tr("panel.restored")


class LockedDoor(Interactable):
    """Une porte de sécurité. La carte d'accès l'ouvre, puis elle disparaît.

    Une porte ouverte est « consommée » : la vue la retire, et MapWithDoors
    cesse de la compter comme un mur pour le monstre.
    """

    def __init__(self, cell: Cell, key_item: str = KEYCARD_ITEM) -> None:
        super().__init__(cell)
        self._key_item = key_item

    @property
    def is_closed(self) -> bool:
        return not self._consumed

    @property
    def prompt(self) -> str:
        return tr("door.prompt")

    def interact(self, player: Player) -> str:
        if not player.inventory.has(self._key_item):
            return tr("door.locked")
        # la carte reste dans l'inventaire : elle ouvre aussi les autres portes
        self._consumed = True
        return tr("door.open")


class Door(Interactable):
    """Une porte normale : E l'ouvre, E la referme. Elle n'est jamais consommée.

    Fermée, elle arrête le monstre, sauf en difficile où il l'ouvre lui-même.
    """

    def __init__(self, cell: Cell) -> None:
        super().__init__(cell)
        self._open = False

    @property
    def is_closed(self) -> bool:
        return not self._open

    @property
    def prompt(self) -> str:
        return tr("door.close_prompt") if self._open else tr("door.open_prompt")

    def reachable_from(self, cell: Cell) -> bool:
        return cell != self.cell  # on ne referme pas une porte sur soi-même

    def interact(self, player: Player) -> str:
        self._open = not self._open
        return ""  # le bruit et le mouvement de la porte suffisent

    def open(self) -> None:
        """Ouverture sans joueur : c'est le monstre qui pousse la porte."""
        self._open = True


class ExitDoor(Interactable):
    """La porte de sortie, verrouillée tant que le courant n'est pas rétabli."""

    def __init__(self, cell: Cell, facility: Facility) -> None:
        super().__init__(cell)
        self._facility = facility

    @property
    def prompt(self) -> str:
        return tr("exit.prompt")

    def interact(self, player: Player) -> str:
        if not self._facility.power_on:
            return tr("exit.locked")
        self._facility.reach_exit()
        return tr("exit.open")


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
            if item is not None and not item.is_consumed and item.reachable_from(cell):
                return item
        return None
