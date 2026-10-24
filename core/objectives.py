"""Objectif courant du joueur, déduit de l'état du jeu. Module indépendant du moteur."""

from core.facility import Facility
from core.inventory import FUSE_ITEM, PANEL_CODE, Inventory
from core.texts import tr


def current_objective(inventory: Inventory, facility: Facility) -> str:
    if facility.exit_reached:
        return tr("objective.escaped")
    if facility.power_on:
        return tr("objective.reach_exit")
    has_fuse = inventory.has(FUSE_ITEM)
    knows_code = inventory.has(PANEL_CODE)
    if not has_fuse and not knows_code:
        return tr("objective.start")
    if not has_fuse:
        return tr("objective.find_fuse")
    if not knows_code:
        return tr("objective.find_code")
    return tr("objective.repair")
