"""The player's inventory: items and knowledge. Engine-independent module."""

FUSE_ITEM = "fuse"
CODE_START = "code start"
CODE_END = "code end"
KEYCARD_ITEM = "keycard"


class Inventory:
    """What the player carries and what they have learned."""

    def __init__(self) -> None:
        self._items: set[str] = set()

    def add(self, item: str) -> None:
        self._items.add(item)

    def has(self, item: str) -> bool:
        return item in self._items

    def remove(self, item: str) -> None:
        if item not in self._items:
            raise KeyError(f"The inventory does not contain '{item}'.")
        self._items.remove(item)
