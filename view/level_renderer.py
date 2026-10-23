"""Construction du bâtiment en 3D à partir d'une FacilityMap.

Ce module affiche ; il ne contient aucune règle du jeu.
"""

from dataclasses import dataclass

from ursina import Entity, color, destroy

from core.level import Cell, FacilityMap
from view.coords import cell_to_world
from view.lighting import make_lit

WALL_HEIGHT = 3.0


@dataclass(frozen=True)
class ItemStyle:
    """Apparence provisoire d'un objet, en attendant de vrais modèles."""

    color: object
    scale: tuple[float, float, float]
    height: float
    solid: bool = False  # un objet solide bloque le joueur


FUSE_STYLE = ItemStyle(color.yellow, (0.25, 0.25, 0.25), 1.0)
POWER_PANEL_STYLE = ItemStyle(color.azure, (0.8, 1.2, 0.3), 1.4)
NOTE_STYLE = ItemStyle(color.white, (0.3, 0.02, 0.4), 0.9)
BATTERY_STYLE = ItemStyle(color.orange, (0.15, 0.3, 0.15), 0.9)
EXIT_STYLE = ItemStyle(color.green, (0.9, 2.4, 0.9), 1.2)
DOCUMENT_STYLE = ItemStyle(color.light_gray, (0.25, 0.02, 0.32), 0.9)
LOCKER_STYLE = ItemStyle(color.dark_gray, (0.9, 2.2, 0.9), 1.1, solid=True)


class LevelRenderer:
    """Construit les murs, le sol, le plafond et les objets d'un niveau."""

    def __init__(self, level: FacilityMap, wall_height: float = WALL_HEIGHT) -> None:
        self._level = level
        self._wall_height = wall_height
        self._items: dict[Cell, Entity] = {}

    def build(self) -> None:
        self._build_floor_and_ceiling()
        self._build_walls()
        self._build_items()

    def remove_item(self, cell: Cell) -> None:
        """Retire l'objet affiché sur une case, par exemple quand il est ramassé."""
        entity = self._items.pop(cell, None)
        if entity is not None:
            destroy(entity)

    def _build_floor_and_ceiling(self) -> None:
        width, height = self._level.width, self._level.height
        center_cell = ((height - 1) / 2, (width - 1) / 2)
        make_lit(
            Entity(
                model="plane",
                scale=(width, 1, height),
                position=cell_to_world(center_cell),
                texture="white_cube",
                texture_scale=(width, height),
                color=color.gray,
                collider="box",
            )
        )
        make_lit(
            Entity(
                model="plane",
                scale=(width, 1, height),
                position=cell_to_world(center_cell, self._wall_height),
                rotation_x=180,
                color=color.dark_gray,
            )
        )

    def _build_walls(self) -> None:
        for cell in self._level.wall_cells():
            make_lit(
                Entity(
                    model="cube",
                    position=cell_to_world(cell, self._wall_height / 2),
                    scale=(1, self._wall_height, 1),
                    texture="white_cube",
                    color=color.light_gray,
                    collider="box",
                )
            )

    def _build_items(self) -> None:
        level = self._level
        placements = [
            (level.fuse_cell, FUSE_STYLE),
            (level.power_panel_cell, POWER_PANEL_STYLE),
            (level.note_cell, NOTE_STYLE),
            (level.exit_cell, EXIT_STYLE),
        ]
        placements += [(cell, BATTERY_STYLE) for cell in level.battery_cells]
        placements += [(cell, DOCUMENT_STYLE) for cell in level.document_cells]
        placements += [(cell, LOCKER_STYLE) for cell in level.hiding_spot_cells]
        for cell, style in placements:
            self._items[cell] = self._spawn_item(cell, style)

    @staticmethod
    def _spawn_item(cell: Cell, style: ItemStyle) -> Entity:
        return make_lit(
            Entity(
                model="cube",
                position=cell_to_world(cell, style.height),
                scale=style.scale,
                color=style.color,
                collider="box" if style.solid else None,
            )
        )
