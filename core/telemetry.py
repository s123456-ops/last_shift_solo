""" Records what heppens during a game, for the statistics """
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.facility import Facility
from core.inventory import CODE_END, CODE_START, FUSE_ITEM, KEYCARD_ITEM, Inventory
from core.level import Cell

OUTCOME_WON = "won"
OUTCOME_CAUGHT = "caught"
OUTCOME_QUIT = "quit"

EVENT_OBJECTIVE = "objective"
EVENT_DOCUMENT = "document"
EVENT_HIDE = "hide"
EVENT_MAP = "map"
EVENT_CAUGHT = "caught"


def reached_steps(inventory: Inventory, facility: Facility) -> list[str]:
       """The steps of the escape the player has reached, in order."""
       reached = {
              "keycard": inventory.has(KEYCARD_ITEM),
        "fuse": inventory.has(FUSE_ITEM) or facility.power_on,
        "code_start": inventory.has(CODE_START),
        "code_end": inventory.has(CODE_END),
        "power": facility.power_on,
              "exit": facility.exit_reached,
       }
       return [step for step, done in reached.items() if done]

@dataclass(frozen=True)
class GameEvent:
       """One thing that happened, at a moment of the game and maybe at a place."""

       kind: str
       at_s: float
       cell: Cell | None = None
       detail: str | None = None

       def to_row(self, run_id: str) -> dict[str, Any]:
              """The row sent to the `events` table."""
              row, col = self.cell if self.cell is not None else (None, None)
              return {
            "run_id": run_id,
            "kind": self.kind,
            "detail": self.detail,
            "at_s": round(self.at_s),
            "cell_row": row,
            "cell_col": col,
        }
@dataclass(frozen=True)
class RunInfo:
               """What is known about a game before it starts."""
               run_id: str
               player_id: str
               game_version: str
               language: str
               mode: str
               difficulty: str
               started_at: datetime



class RunRecorder:
    """Collects the facts of one game."""

    def __init__(self) -> None:
        self._events: list[GameEvent] = []
        self._documents_read: set[Cell] = set()
        self._steps: list[str] = []

    @property
    def events(self) -> tuple[GameEvent, ...]:
        return tuple(self._events)

    def record_hide(self, cell: Cell, at_s: float) -> None:
        self._events.append(GameEvent(EVENT_HIDE, at_s, cell))

    def record_map(self, at_s: float) -> None:
        self._events.append(GameEvent(EVENT_MAP, at_s))

    def record_caught(self, cell: Cell, at_s: float) -> None:
        self._events.append(GameEvent(EVENT_CAUGHT, at_s, cell))
    
    def record_document(self, cell: Cell, at_s: float) -> None:
        """A document counts once, even if the player reads it again."""
        if cell in self._documents_read:
            return
        self._documents_read.add(cell)
        self._events.append(GameEvent(EVENT_DOCUMENT, at_s, cell))
    
    @property
    def steps(self) -> tuple[str, ...]:
        return tuple(self._steps)

    def record_progress(
        self, inventory: Inventory, facility: Facility, at_s: float, cell: Cell
    ) -> None:
        """Notes every step reached for the first time."""
        for step in reached_steps(inventory, facility):
            if step not in self._steps:
                self._steps.append(step)
                self._events.append(GameEvent(EVENT_OBJECTIVE, at_s, cell, step))
    
    def count(self, kind: str) -> int:
        return sum(1 for event in self._events if event.kind == kind)

    def run_row(self, info: RunInfo, outcome: str, duration_s: float) -> dict[str, Any]:
        """The row sent to the `runs` table."""
        return {
            "run_id": info.run_id,
            "player_id": info.player_id,
            "game_version": info.game_version,
            "language": info.language,
            "mode": info.mode,
            "difficulty": info.difficulty,
            "started_at": info.started_at.isoformat(),
            "duration_s": round(duration_s),
            "outcome": outcome,
            "steps_done": list(self._steps),
            "documents_read": self.count(EVENT_DOCUMENT),
            "hides": self.count(EVENT_HIDE),
            "map_opens": self.count(EVENT_MAP),
        }

    def event_rows(self, run_id: str) -> list[dict[str, Any]]:
        return [event.to_row(run_id) for event in self._events]