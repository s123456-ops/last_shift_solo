"""Inventaire du joueur : objets et connaissances. Module indépendant du moteur de jeu."""

FUSE_ITEM = "fusible"
CODE_START = "code du tableau"
CODE_END = "fin du code"
KEYCARD_ITEM = "carte d'accès"


class Inventory:
    """Les objets que le joueur porte et ce qu'il a appris."""

    def __init__(self) -> None:
        self._items: set[str] = set()

    def add(self, item: str) -> None:
        self._items.add(item)

    def has(self, item: str) -> bool:
        return item in self._items

    def remove(self, item: str) -> None:
        if item not in self._items:
            raise KeyError(f"L'inventaire ne contient pas « {item} ».")
        self._items.remove(item)
