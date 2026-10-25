"""Objectif courant du joueur, déduit de l'état du jeu. Module indépendant du moteur."""

from core.facility import Facility
from core.inventory import CODE_END, CODE_START, FUSE_ITEM, Inventory
from core.texts import tr


def current_objective(inventory: Inventory, facility: Facility) -> str:
    if facility.exit_reached:
        return tr("objective.escaped")
    if facility.power_on:
        return tr("objective.reach_exit")
    has_fuse = inventory.has(FUSE_ITEM)
    knows_code = inventory.has(CODE_START) and inventory.has(CODE_END)
    if not has_fuse and not knows_code:
        return tr("objective.start")
    if not has_fuse:
        return tr("objective.find_fuse")
    if not knows_code:
        if inventory.has(CODE_START):
            return tr("objective.find_code_end")
        return tr("objective.find_code")
    return tr("objective.repair")
