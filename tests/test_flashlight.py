from core.flashlight import  Flashlight

"""Test the flashlight functionality.
-new lamp off and full (max camacity 100, with drain per sec= 10)
-player can toggle on/off flashlight
-battery drains only when flashlight is on (drain per se x dt) for every update (dt)
- when battery gets to zero, flashlight is off automatically, and it never goes below zero (this is super important!)
-and ofc a flashlight cant turn on if battery is zero

"""
def test_new_flashlight_is_off_and_full():
    light= Flashlight(capacity=100, drain_per_second=10)
    assert not light.is_on
    assert light.battery == 100

def test_toggle_switches_the_light_on_and_off():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    assert light.is_on
    light.toggle()
    assert not light.is_on

def test_battery_does_not_drain_when_off():
    light=Flashlight(capacity=100, drain_per_second=10)
    light.update(dt=5)
    assert light.battery == 100

def test_battery_drains_when_on():
    light=Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=3)
    assert light.battery== 70

def test_battery_never_goes_below_zero():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=15)  # would drain more than the battery's capacity, therefore it would be easy to detect if it goes below zero)
    assert light.battery == 0
    assert not light.is_on

def test_flashlight_cant_turn_on_if_battery_is_zero():
    light= Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=10) # battery drained to zero
    assert light.battery == 0
    light.toggle() #to try and turn it on again
    assert not light.is_on

def test_recharge_never_exceeds_capacity():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=1)  # batterie à 90
    light.recharge(20)  # il ne manque que 10
    assert light.battery == 100

def test_recharge_adds_battery():
    light = Flashlight(capacity=100, drain_per_second=10)
    light.toggle()
    light.update(dt=5)  # batterie à 50
    light.recharge(30)
    assert light.battery == 80