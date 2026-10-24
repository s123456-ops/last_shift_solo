import pytest

from core.facility import Facility
from core.flashlight import Flashlight
from core.interactables import (
    BatteryPickup,
    ExitDoor,
    HidingSpot,
    Interactable,
    Interactions,
    Note,
    Pickup,
    PowerPanel,
)
from core.inventory import FUSE_ITEM, PANEL_CODE
from core.player import Player
from core.stamina import Stamina


def make_player_with_low_battery():
    flashlight = Flashlight(capacity=100, drain_per_second=10)
    flashlight.toggle()
    flashlight.update(dt=8)  # batterie à 20
    return Player(
        flashlight, Stamina(capacity=100, drain_per_second=10, regen_per_second=5)
    )


def test_battery_recharges_the_flashlight():
    player = make_player_with_low_battery()
    BatteryPickup((1, 1), charge=40).interact(player)
    assert player.flashlight.battery == 60


def test_battery_is_consumed_after_use():
    battery = BatteryPickup((1, 1))
    battery.interact(make_player_with_low_battery())
    assert battery.is_consumed


def test_item_on_adjacent_cell_is_within_reach():
    battery = BatteryPickup((2, 2))
    assert Interactions([battery]).near((2, 3)) is battery


def test_item_on_diagonal_cell_is_out_of_reach():
    assert Interactions([BatteryPickup((2, 2))]).near((3, 3)) is None


def test_consumed_item_is_no_longer_within_reach():
    battery = BatteryPickup((2, 2))
    battery.interact(make_player_with_low_battery())
    assert Interactions([battery]).near((2, 2)) is None


def test_two_items_on_the_same_cell_raise():
    with pytest.raises(ValueError, match="Deux objets"):
        Interactions([BatteryPickup((2, 2)), BatteryPickup((2, 2))])


def test_interactable_cannot_be_created_directly():
    with pytest.raises(TypeError):
        Interactable((0, 0))


def test_hiding_spot_hides_then_releases_the_player():
    player = make_player_with_low_battery()
    locker = HidingSpot((3, 3))
    locker.interact(player)
    assert player.is_hidden
    locker.interact(player)
    assert not player.is_hidden


def test_hiding_turns_the_flashlight_off():
    player = make_player_with_low_battery()
    assert player.flashlight.is_on
    HidingSpot((3, 3)).interact(player)
    assert not player.flashlight.is_on


def test_hiding_spot_prompt_changes_when_occupied():
    locker = HidingSpot((3, 3))
    assert locker.prompt == "Se cacher dans le casier"
    locker.interact(make_player_with_low_battery())
    assert locker.prompt == "Sortir du casier"


def test_hiding_spot_is_never_consumed():
    locker = HidingSpot((3, 3))
    locker.interact(make_player_with_low_battery())
    assert not locker.is_consumed


def make_fuse():
    return Pickup((1, 1), FUSE_ITEM, "Ramasser le fusible", "Fusible récupéré.")


def test_pickup_adds_the_item_to_the_inventory():
    player = make_player_with_low_battery()
    fuse = make_fuse()
    fuse.interact(player)
    assert player.inventory.has(FUSE_ITEM)
    assert fuse.is_consumed


def test_reading_the_code_note_teaches_the_code():
    player = make_player_with_low_battery()
    Note((1, 1), "Note de Morel", "Code : 4 7 1", grants=PANEL_CODE).interact(player)
    assert player.inventory.has(PANEL_CODE)


def test_panel_refuses_without_a_fuse():
    player = make_player_with_low_battery()
    facility = Facility()
    PowerPanel((1, 1), facility).interact(player)
    assert not facility.power_on


def test_panel_refuses_without_the_code():
    player = make_player_with_low_battery()
    player.inventory.add(FUSE_ITEM)
    facility = Facility()
    PowerPanel((1, 1), facility).interact(player)
    assert not facility.power_on


def test_panel_restores_power_with_fuse_and_code():
    player = make_player_with_low_battery()
    player.inventory.add(FUSE_ITEM)
    player.inventory.add(PANEL_CODE)
    facility = Facility()
    PowerPanel((1, 1), facility).interact(player)
    assert facility.power_on
    assert not player.inventory.has(FUSE_ITEM)  # le fusible a été utilisé


def test_exit_door_stays_locked_without_power():
    facility = Facility()
    ExitDoor((1, 1), facility).interact(make_player_with_low_battery())
    assert not facility.exit_reached


def test_exit_door_opens_once_power_is_restored():
    facility = Facility()
    facility.restore_power()
    ExitDoor((1, 1), facility).interact(make_player_with_low_battery())
    assert facility.exit_reached


def test_notes_are_readable():
    assert Note((1, 1), "Titre", "Texte").is_readable


def test_batteries_are_not_readable():
    assert not BatteryPickup((1, 1)).is_readable
