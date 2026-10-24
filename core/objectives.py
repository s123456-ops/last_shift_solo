"""Objectif courant du joueur, déduit de l'état du jeu. Module indépendant du moteur."""

from core.facility import Facility
from core.inventory import FUSE_ITEM, PANEL_CODE, Inventory


def current_objective(inventory: Inventory, facility: Facility) -> str:
    if facility.exit_reached:
        return "Vous êtes sorti."
    if facility.power_on:
        return "Rejoindre la sortie."
    has_fuse = inventory.has(FUSE_ITEM)
    knows_code = inventory.has(PANEL_CODE)
    if not has_fuse and not knows_code:
        return "Rétablir le courant : trouver un fusible et le code du tableau."
    if not has_fuse:
        return "Trouver un fusible de rechange."
    if not knows_code:
        return "Trouver le code du tableau électrique."
    return "Réparer le tableau électrique, en salle de maintenance."
