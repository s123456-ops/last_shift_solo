import pytest

from core.flashlight import Flashlight
from core.interactables import BatteryPickup, HidingSpot, Interactable, Interactions
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
