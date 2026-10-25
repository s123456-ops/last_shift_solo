"""Monster behaviour: patrol, chase, search (State pattern).

Engine-independent module.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.level import Cell, Obstacles
from core.pathfinding import Pathfinder
from core.perception import can_hear, can_see

SEARCH_STEPS = 6  # steps spent searching on the spot before giving up


@dataclass(frozen=True)
class Situation:
    """What the monster can know about the player at a given moment."""

    player_cell: Cell
    player_running: bool
    flashlight_on: bool
    player_hidden: bool = False


class MonsterState(ABC):
    """A monster state: it decides the transition, then the next cell."""

    @abstractmethod
    def next_state(
        self, monster: "Monster", perceives_player: bool, situation: Situation
    ) -> "MonsterState": ...

    @abstractmethod
    def next_cell(self, monster: "Monster") -> Cell: ...


class Patrol(MonsterState):
    """Follows its route and ignores the player until it perceives them."""

    def __init__(self, route: tuple[Cell, ...]) -> None:
        self._route = route
        self._index = 0

    def next_state(self, monster, perceives_player, situation):
        if perceives_player:
            return Chase(situation.player_cell)
        return self

    def next_cell(self, monster):
        if monster.cell == self._route[self._index]:
            self._index = (self._index + 1) % len(self._route)
        return monster.pathfinder.next_step(monster.cell, self._route[self._index])


class Chase(MonsterState):
    """Rushes towards the last position where it perceived the player."""

    def __init__(self, last_seen: Cell) -> None:
        self._last_seen = last_seen

    def next_state(self, monster, perceives_player, situation):
        if perceives_player:
            self._last_seen = situation.player_cell
            return self
        return Search(self._last_seen)

    def next_cell(self, monster):
        return monster.pathfinder.next_step(monster.cell, self._last_seen)


class Search(MonsterState):
    """Goes to the last known position, searches for a while, then resumes its patrol."""

    def __init__(self, last_seen: Cell, steps: int = SEARCH_STEPS) -> None:
        self._last_seen = last_seen
        self._steps_left = steps

    def next_state(self, monster, perceives_player, situation):
        if perceives_player:
            return Chase(situation.player_cell)
        if self._steps_left <= 0:
            return Patrol(monster.patrol_route)
        return self

    def next_cell(self, monster):
        step = monster.pathfinder.next_step(monster.cell, self._last_seen)
        if step == monster.cell:  # arrived, or no path: it searches
            self._steps_left -= 1
        return step


class Monster:
    """The monster: its position, its senses and its current state."""

    def __init__(
        self,
        level: Obstacles,
        start: Cell,
        patrol_route: list[Cell],
        sight_with_light: float = 8,
        sight_in_dark: float = 4,
        hearing_range: float = 6,
    ) -> None:
        if not patrol_route:
            raise ValueError(
                "The monster's patrol route must contain at least one cell."
            )
        for cell in patrol_route:
            if level.is_wall(cell):
                raise ValueError(
                    f"The monster's patrol route goes through a wall: {cell}."
                )
        self._level = level
        self._pathfinder = Pathfinder(level)
        self._cell = start
        self._patrol_route = tuple(patrol_route)
        self._sight_with_light = sight_with_light
        self._sight_in_dark = sight_in_dark
        self._hearing_range = hearing_range
        self._state: MonsterState = Patrol(self._patrol_route)

    @property
    def cell(self) -> Cell:
        return self._cell

    @property
    def state(self) -> MonsterState:
        return self._state

    @property
    def pathfinder(self) -> Pathfinder:
        return self._pathfinder

    @property
    def patrol_route(self) -> tuple[Cell, ...]:
        return self._patrol_route

    @property
    def is_chasing(self) -> bool:
        return isinstance(self._state, Chase)

    @property
    def is_searching(self) -> bool:
        return isinstance(self._state, Search)

    def perceives(self, situation: Situation) -> bool:
        if situation.player_hidden:
            return self.is_chasing  # it saw you get in: it knows where you are
        sight = (
            self._sight_with_light if situation.flashlight_on else self._sight_in_dark
        )
        if can_see(self._level, self._cell, situation.player_cell, sight):
            return True
        return situation.player_running and can_hear(
            self._cell, situation.player_cell, self._hearing_range
        )

    def step(self, situation: Situation) -> Cell:
        """Called each time the monster reaches a cell: decides the next one."""
        self._state = self._state.next_state(self, self.perceives(situation), situation)
        self._cell = self._state.next_cell(self)
        return self._cell
