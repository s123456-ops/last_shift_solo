from core.flashlight import Flashlight


def test_new_flashlight_is_off_and_full():
    light = Flashlight(capacity=100, drain_per_second=10)
    assert not light.is_on
    assert light.battery == 100


def test_toggle_switches_the_light_on_and_off():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    assert light.is_on
    light.toggle()
    assert not light.is_on


def test_battery_does_not_drain_when_off():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.update(dt=5)
    assert light.battery == 100


def test_battery_drains_while_on():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=3)
    assert light.battery == 70


def test_empty_battery_stops_at_zero_and_turns_light_off():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=15)  # consommerait 150, plus que la batterie disponible
    assert light.battery == 0
    assert not light.is_on


def test_flashlight_cannot_turn_on_with_empty_battery():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=10)  # consomme exactement les 100 de la batterie
    assert light.battery == 0
    light.toggle()  # tentative de rallumage
    assert not light.is_on


def test_recharge_adds_battery():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=5)  # batterie à 50
    light.recharge(30)
    assert light.battery == 80


def test_recharge_never_exceeds_capacity():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=1)  # batterie à 90
    light.recharge(20)  # il ne manque que 10
    assert light.battery == 100


def test_charge_ratio_reflects_remaining_battery():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=2.5)  # consomme 25
    assert light.charge_ratio == 0.75
