"""Game in progress: gathers the rules and decides victory or defeat.

Engine-independent module.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto

from core.facility import Facility
from core.interactables import Door, Interactable, Interactions
from core.level import Cell
from core.monster import Monster, Situation
from core.objectives import current_objective
from core.player import Player


class GameStatus(Enum):
    PLAYING = auto()
    WON = auto()
    LOST = auto()


@dataclass(frozen=True)
class InteractionResult:
    """What happened when the player pressed E."""

    item: Interactable
    message: str


class GameSession:
    """The conductor of the rules. The view queries it, but never decides."""

    def __init__(
        self,
        player: Player,
        monster: Monster,
        interactions: Interactions,
        facility: Facility,
        grace_period: float = 20.0,
        peaceful: bool = False,
        doors: Sequence[Door] = (),
        monster_opens_doors: bool = False,
    ) -> None:
        self._player = player
        self._monster = monster
        self._interactions = interactions
        self._facility = facility
        self._grace_period = grace_period
        self._peaceful = peaceful
        self._doors = tuple(doors)
        self._monster_opens_doors = monster_opens_doors
        self._elapsed = 0.0
        self._status = GameStatus.PLAYING

    @property
    def player(self) -> Player:
        return self._player

    @property
    def status(self) -> GameStatus:
        return self._status

    @property
    def is_over(self) -> bool:
        return self._status is not GameStatus.PLAYING

    @property
    def objective(self) -> str:
        return current_objective(self._player.inventory, self._facility)

    @property
    def monster_is_active(self) -> bool:
        return not self._peaceful and self._elapsed >= self._grace_period

    @property
    def monster_is_chasing(self) -> bool:
        return self._monster.is_chasing

    @property
    def monster_is_searching(self) -> bool:
        return self._monster.is_searching

    @property
    def doors(self) -> tuple[Door, ...]:
        """The regular doors, so the view can show them open or closed."""
        return self._doors

    @property
    def power_on(self) -> bool:
        return self._facility.power_on

    def update(self, dt: float, wants_to_run: bool) -> None:
        if self.is_over:
            return
        self._elapsed += dt
        self._player.flashlight.update(dt)
        self._player.stamina.update(dt, wants_to_run)

    def toggle_flashlight(self) -> None:
        if self.is_over or self._player.is_hidden:
            return
        self._player.flashlight.toggle()

    def item_near(self, cell: Cell) -> Interactable | None:
        if self.is_over:
            return None
        return self._interactions.near(cell)

    def interact(self, cell: Cell) -> InteractionResult | None:
        item = self.item_near(cell)
        if item is None:
            return None
        message = item.interact(self._player)
        if self._facility.exit_reached:
            self._status = GameStatus.WON
        return InteractionResult(item, message)

    def next_monster_cell(self, player_cell: Cell) -> Cell | None:
        """The monster's next cell, or None if it must not move yet."""
        if self.is_over or not self.monster_is_active:
            return None
        situation = Situation(
            player_cell=player_cell,
            player_running=self._player.stamina.is_running,
            flashlight_on=self._player.flashlight.is_on,
            player_hidden=self._player.is_hidden,
        )
        cell = self._monster.step(situation)
        if self._monster_opens_doors:
            self._force_door(cell)
        return cell

    def _force_door(self, cell: Cell) -> None:
        """In hard mode, the monster opens the closed door it is about to cross."""
        for door in self._doors:
            if door.cell == cell and door.is_closed:
                door.open()

    def report_caught(self) -> None:
        """The view detected the contact; the session decides that the game is lost."""
        if not self.is_over:
            self._status = GameStatus.LOST
