from core.doors import MapWithDoors
from core.flashlight import Flashlight
from core.interactables import Door, LockedDoor
from core.inventory import KEYCARD_ITEM
from core.level import parse_level
from core.monster import Monster, Situation
from core.pathfinding import Pathfinder
from core.player import Player
from core.stamina import Stamina

# Deux pièces reliées par une seule porte de sécurité, en (2, 4).
LEVEL = parse_level("""
#########
#P.F#G.E#
#K.NS..M#
#########
""")
DOOR_CELL = (2, 4)


def make_map():
    door = LockedDoor(DOOR_CELL)
    return MapWithDoors(LEVEL, [door]), door


def open_door(door):
    player = Player(
        Flashlight(capacity=100, drain_per_second=10),
        Stamina(capacity=100, drain_per_second=10, regen_per_second=5),
    )
    player.inventory.add(KEYCARD_ITEM)
    door.interact(player)


def test_closed_door_blocks_like_a_wall():
    building, _ = make_map()
    assert building.is_wall(DOOR_CELL)


def test_open_door_lets_through():
    building, door = make_map()
    open_door(door)
    assert not building.is_wall(DOOR_CELL)


def test_walls_of_the_original_map_still_block():
    building, door = make_map()
    open_door(door)
    assert building.is_wall((1, 4))
    assert not building.is_wall((1, 1))


def test_no_path_through_a_closed_door():
    building, _ = make_map()
    assert Pathfinder(building).find_path((2, 7), (2, 1)) == []


def test_path_goes_through_the_door_once_open():
    building, door = make_map()
    open_door(door)
    assert DOOR_CELL in Pathfinder(building).find_path((2, 7), (2, 1))


def test_monster_cannot_see_through_a_closed_door():
    building, _ = make_map()
    monster = Monster(building, start=(2, 6), patrol_route=[(2, 6)])
    situation = Situation(player_cell=(2, 2), player_running=False, flashlight_on=True)
    assert not monster.perceives(situation)


def test_monster_sees_through_the_open_door():
    building, door = make_map()
    open_door(door)
    monster = Monster(building, start=(2, 6), patrol_route=[(2, 6)])
    situation = Situation(player_cell=(2, 2), player_running=False, flashlight_on=True)
    assert monster.perceives(situation)


def test_closed_normal_door_blocks_the_monster():
    door = Door(DOOR_CELL)
    building = MapWithDoors(LEVEL, [door])
    assert Pathfinder(building).find_path((2, 7), (2, 1)) == []


def test_monster_can_leave_a_door_closed_on_him():
    building, _ = make_map()
    assert Pathfinder(building).find_path(DOOR_CELL, (2, 7))
