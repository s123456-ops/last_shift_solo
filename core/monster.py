"""Comportement du monstre : patrouille, poursuite, recherche (patron State).

Module indépendant du moteur de jeu.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.level import Cell, Obstacles
from core.pathfinding import Pathfinder
from core.perception import can_hear, can_see

SEARCH_STEPS = 6  # nombre de pas passés à chercher sur place avant d'abandonner


@dataclass(frozen=True)
class Situation:
    """Ce que le monstre peut savoir du joueur à un instant donné."""

    player_cell: Cell
    player_running: bool
    flashlight_on: bool
    player_hidden: bool = False


class MonsterState(ABC):
    """Un état du monstre : il décide de la transition, puis de la prochaine case."""

    @abstractmethod
    def next_state(
        self, monster: "Monster", perceives_player: bool, situation: Situation
    ) -> "MonsterState": ...

    @abstractmethod
    def next_cell(self, monster: "Monster") -> Cell: ...


class Patrol(MonsterState):
    """Suit sa ronde et ignore le joueur tant qu'il ne le perçoit pas."""

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
    """Fonce vers la dernière position où il a perçu le joueur."""

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
    """Va à la dernière position connue, cherche un moment, puis reprend sa ronde."""

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
        if step == monster.cell:  # arrivé sur place, ou chemin impossible : il cherche
            self._steps_left -= 1
        return step


class Monster:
    """Le monstre : sa position, ses sens et son état courant."""

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
            raise ValueError("La ronde du monstre doit contenir au moins une case.")
        for cell in patrol_route:
            if level.is_wall(cell):
                raise ValueError(f"La ronde du monstre passe par un mur : {cell}.")
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
            return self.is_chasing  # il vous a vu entrer : il sait où vous êtes
        sight = (
            self._sight_with_light if situation.flashlight_on else self._sight_in_dark
        )
        if can_see(self._level, self._cell, situation.player_cell, sight):
            return True
        return situation.player_running and can_hear(
            self._cell, situation.player_cell, self._hearing_range
        )

    def step(self, situation: Situation) -> Cell:
        """Appelé chaque fois que le monstre atteint une case : décide de la suivante."""
        self._state = self._state.next_state(self, self.perceives(situation), situation)
        self._cell = self._state.next_cell(self)
        return self._cell
