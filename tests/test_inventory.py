import pytest

from core.inventory import Inventory


def test_new_inventory_is_empty():
    assert not Inventory().has("fuse")


def test_added_item_is_found():
    inventory = Inventory()
    inventory.add("fuse")
    assert inventory.has("fuse")


def test_removing_a_missing_item_raises():
    with pytest.raises(KeyError):
        Inventory().remove("fuse")
