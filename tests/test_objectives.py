from core.facility import Facility
from core.inventory import CODE_END, CODE_START, FUSE_ITEM, Inventory
from core.objectives import current_objective


def test_objective_at_the_start_mentions_fuse_and_code():
    objective = current_objective(Inventory(), Facility())
    assert "fuse" in objective and "code" in objective


def test_objective_with_fuse_only_asks_for_the_code():
    inventory = Inventory()
    inventory.add(FUSE_ITEM)
    assert current_objective(inventory, Facility()) == "Find the generator code."


def test_objective_with_fuse_and_code_asks_to_repair_the_panel():
    inventory = Inventory()
    inventory.add(FUSE_ITEM)
    inventory.add(CODE_START)
    inventory.add(CODE_END)
    assert "Repair" in current_objective(inventory, Facility())


def test_objective_once_power_is_restored_is_the_exit():
    facility = Facility()
    facility.restore_power()
    assert current_objective(Inventory(), facility) == "Get to the exit."


def test_objective_with_first_half_of_the_code_asks_for_the_last_digit():
    inventory = Inventory()
    inventory.add(FUSE_ITEM)
    inventory.add(CODE_START)
    assert (
        current_objective(inventory, Facility()) == "Find the last digit of the code."
    )
