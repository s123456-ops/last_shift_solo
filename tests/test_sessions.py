from core.facility import Facility
from core.flashlight import Flashlight
from core.interactables import ExitDoor, Interactions, Note, Pickup, PowerPanel
from core.inventory import FUSE_ITEM, PANEL_CODE
from core.level import parse_level
from core.monster import Monster
from core.player import Player
from core.session import GameSession, GameStatus
from core.stamina import Stamina

LEVEL = parse_level("""
#########
#.......#
#P..#..M#
#.......#
#EFG..N.#
#########
""")


def make_session(**options):
    player = Player(
        Flashlight(capacity=100, drain_per_second=10),
        Stamina(capacity=100, drain_per_second=10, regen_per_second=5),
    )
    facility = Facility()
    interactions = Interactions(
        [
            Pickup((4, 2), FUSE_ITEM, "Ramasser le fusible", "Fusible récupéré."),
            Note((4, 6), "Note", "Code : 4 7 1", grants=PANEL_CODE),
            PowerPanel((4, 3), facility),
            ExitDoor((4, 1), facility),
        ]
    )
    monster = Monster(LEVEL, start=(2, 7), patrol_route=[(2, 7), (3, 7)])
    return GameSession(player, monster, interactions, facility, **options)


def test_session_starts_in_play():
    assert make_session().status is GameStatus.PLAYING


def test_monster_waits_during_the_grace_period():
    session = make_session(grace_period=20)
    session.update(dt=10, wants_to_run=False)
    assert session.next_monster_cell((2, 1)) is None


def test_monster_moves_after_the_grace_period():
    session = make_session(grace_period=20)
    session.update(dt=21, wants_to_run=False)
    assert session.next_monster_cell((2, 1)) is not None


def test_monster_never_moves_in_peaceful_mode():
    session = make_session(peaceful=True)
    session.update(dt=100, wants_to_run=False)
    assert session.next_monster_cell((2, 1)) is None


def test_being_caught_loses_the_game():
    session = make_session()
    session.report_caught()
    assert session.status is GameStatus.LOST


def test_nothing_changes_once_the_game_is_over():
    session = make_session()
    session.report_caught()
    session.toggle_flashlight()
    assert not session.player.flashlight.is_on


def test_full_objective_sequence_wins_the_game():
    session = make_session()
    session.interact((4, 2))  # fusible
    session.interact((4, 6))  # note : le code
    session.interact((4, 3))  # tableau électrique
    session.interact((4, 1))  # porte de sortie
    assert session.status is GameStatus.WON


def test_exit_without_power_does_not_win():
    session = make_session()
    session.interact((4, 1))
    assert session.status is GameStatus.PLAYING

def test_power_on_reflects_the_repaired_panel():
    session = make_session()
    assert not session.power_on
    session.interact((4, 2))   # fusible
    session.interact((4, 6))   # code
    session.interact((4, 3))   # tableau
    assert session.power_on