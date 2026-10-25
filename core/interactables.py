"""Objects the player interacts with (E key).

Engine-independent module.
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
)  # the player's cell and its 4 neighbours


class Interactable(ABC):
    """An object placed on a cell. Each subclass defines its own effect."""

    def __init__(self, cell: Cell) -> None:
        self._cell = cell
        self._consumed = False

    @property
    def cell(self) -> Cell:
        return self._cell

    @property
    def is_consumed(self) -> bool:
        """True once the object has been used and must disappear."""
        return self._consumed

    @property
    def is_readable(self) -> bool:
        """True if interacting opens a text to read, shown full screen."""
        return False

    def reachable_from(self, cell: Cell) -> bool:
        """Can the player, standing on this cell, use the object? Yes by default."""
        return True

    @property
    @abstractmethod
    def prompt(self) -> str:
        """Text shown when the player is within reach."""

    @abstractmethod
    def interact(self, player: Player) -> str:
        """Applies the object's effect and returns the message to display."""


class BatteryPickup(Interactable):
    """A battery that recharges the flashlight, single use."""

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
    """A locker to hide in. It is never consumed: the player can come back."""

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
    """An object to pick up, which goes into the inventory (the fuse)."""

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
    """A text to read, which may teach the player something (the code)."""

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
    """The generator: fuse + full code = power restored."""

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
    """A security door. The keycard opens it, then it disappears.

    An open door is "consumed": the view removes it, and MapWithDoors
    stops counting it as a wall for the monster.
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
        # the keycard stays in the inventory: it also opens the other doors
        self._consumed = True
        return tr("door.open")


class Door(Interactable):
    """A regular door: E opens it, E closes it again. It is never consumed.

    When closed, it stops the monster, except in hard mode where it opens doors itself.
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
        return cell != self.cell  # you don't close a door on yourself

    def interact(self, player: Player) -> str:
        self._open = not self._open
        return ""  # the door's sound and movement are enough

    def open(self) -> None:
        """Opening without the player: the monster pushes the door."""
        self._open = True


class ExitDoor(Interactable):
    """The exit door, locked until the power is restored."""

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
    """The level's objects, looked up by cell."""

    def __init__(self, items: list[Interactable]) -> None:
        self._items: dict[Cell, Interactable] = {}
        for item in items:
            if item.cell in self._items:
                raise ValueError(f"Two objects on cell {item.cell}.")
            self._items[item.cell] = item

    def near(self, cell: Cell) -> Interactable | None:
        """The object still available on the player's cell or a neighbouring cell."""
        row, col = cell
        for d_row, d_col in REACH:
            item = self._items.get((row + d_row, col + d_col))
            if item is not None and not item.is_consumed and item.reachable_from(cell):
                return item
        return None
