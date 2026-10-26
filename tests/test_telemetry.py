from datetime import UTC, datetime

from core.facility import Facility
from core.inventory import CODE_START, KEYCARD_ITEM, Inventory
from core.telemetry import (
    EVENT_CAUGHT,
    EVENT_MAP,
    OUTCOME_CAUGHT,
    GameEvent,
    RunInfo,
    RunRecorder,
    reached_steps,
)


def test_no_step_is_reached_at_the_start():
    assert reached_steps(Inventory(), Facility()) == []

def test_the_fuse_step_stays_reached_once_installed():
    facility = Facility()
    facility.restore_power()
    assert "fuse" in reached_steps(Inventory(),facility)



def test_an_event_becomes_a_database_row():
    event = GameEvent(EVENT_CAUGHT, at_s=312.6, cell=(15, 28))
    assert event.to_row("run-1") == {
        "run_id": "run-1",
        "kind": "caught",
        "detail": None,
        "at_s": 313,
        "cell_row": 15,
        "cell_col": 28,
    }


def test_an_event_without_a_place_has_empty_coordinates():
    row = GameEvent(EVENT_MAP, at_s=60).to_row("run-1")
    assert row["cell_row"] is None
    assert row["cell_col"] is None



def test_the_recorder_keeps_events_in_order():
    recorder = RunRecorder()
    recorder.record_map(at_s=60)
    recorder.record_caught((15, 28), at_s=312)
    kinds = [event.kind for event in recorder.events]
    assert kinds == ["map", "caught"]


def test_a_document_read_twice_counts_once():
    recorder = RunRecorder()
    recorder.record_document((15, 28), at_s=100)
    recorder.record_document((15, 28), at_s=200)
    recorder.record_document((1, 17), at_s=300)
    assert len(recorder.events) == 2



def test_each_step_is_recorded_once_in_the_order_it_was_reached():
    inventory, facility, recorder = Inventory(), Facility(), RunRecorder()
    inventory.add(CODE_START)
    recorder.record_progress(inventory, facility, at_s=10, cell=(1, 1))
    inventory.add(KEYCARD_ITEM)
    recorder.record_progress(inventory, facility, at_s=20, cell=(2, 2))
    recorder.record_progress(inventory, facility, at_s=30, cell=(3, 3))
    assert recorder.steps == ("code_start", "keycard")



def test_the_run_row_summarises_the_game():
    info = RunInfo(
        run_id="run-1",
        player_id="player-1",
        game_version="0.2.0",
        language="en",
        mode="survival",
        difficulty="normal",
        started_at=datetime(2026, 10, 26, 12, 0, tzinfo=UTC),
    )
    recorder = RunRecorder()
    recorder.record_hide((5, 7), at_s=50)
    recorder.record_map(at_s=60)
    recorder.record_map(at_s=70)
    row = recorder.run_row(info, OUTCOME_CAUGHT, duration_s=312.6)
    assert row["outcome"] == "caught"
    assert row["duration_s"] == 313
    assert row["hides"] == 1
    assert row["map_opens"] == 2
    assert row["started_at"] == "2026-10-26T12:00:00+00:00"