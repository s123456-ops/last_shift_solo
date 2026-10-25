"""Partie en cours : rassemble les règles et décide de la victoire ou de la défaite.

Module indépendant du moteur de jeu.
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
    """Ce qui s'est passé quand le joueur a appuyé sur E."""

    item: Interactable
    message: str


class GameSession:
    """Le chef d'orchestre des règles. La vue l'interroge, mais ne décide jamais."""

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
        """Les portes normales, pour que la vue les affiche ouvertes ou fermées."""
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
        """La prochaine case du monstre, ou None s'il ne doit pas encore bouger."""
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
        """En difficile, le monstre ouvre la porte fermée qu'il s'apprête à franchir."""
        for door in self._doors:
            if door.cell == cell and door.is_closed:
                door.open()

    def report_caught(self) -> None:
        """La vue a détecté le contact ; c'est la session qui décide de la défaite."""
        if not self.is_over:
            self._status = GameStatus.LOST
