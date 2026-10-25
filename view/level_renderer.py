"""Construction du bâtiment en 3D à partir d'une FacilityMap.

Ce module affiche ; il ne contient aucune règle du jeu.
"""

from dataclasses import dataclass

from ursina import Entity, Vec3, color, destroy

from core.level import Cell, FacilityMap
from view.coords import cell_to_world
from view.furniture import DESK, SHELF, FurnitureStyle, place_furniture
from view.lighting import make_lit

WALL_HEIGHT = 3.0
# Textures générées par tools/make_textures.py, rangées dans assets/textures/.
FLOOR_TEXTURE = "floor_tiles"
WALL_TEXTURE = "wall_tiles"  # dessinée pour un mur entier : 1 case de large, 3 de haut
CEILING_TEXTURE = "ceiling_tiles"


@dataclass(frozen=True)
class ItemStyle:
    """Apparence provisoire d'un objet, en attendant de vrais modèles."""

    color: object
    scale: tuple[float, float, float]
    height: float
    solid: bool = False  # un objet solide bloque le joueur
    support: FurnitureStyle | None = None  # le meuble sur lequel l'objet est posé


FUSE_STYLE = ItemStyle(color.yellow, (0.25, 0.25, 0.25), 1.0, support=SHELF)
POWER_PANEL_STYLE = ItemStyle(color.azure, (0.8, 1.2, 0.3), 1.4)
NOTE_STYLE = ItemStyle(color.white, (0.3, 0.02, 0.4), 0.9, support=DESK)
BATTERY_STYLE = ItemStyle(color.orange, (0.15, 0.3, 0.15), 0.9, support=SHELF)
EXIT_STYLE = ItemStyle(color.green, (0.9, 2.4, 0.9), 1.2)
DOCUMENT_STYLE = ItemStyle(color.light_gray, (0.25, 0.02, 0.32), 0.9, support=DESK)
LOCKER_STYLE = ItemStyle(color.dark_gray, (0.9, 2.2, 0.9), 1.1, solid=True)
KEYCARD_STYLE = ItemStyle(color.cyan, (0.3, 0.02, 0.2), 0.9, support=DESK)
SECURITY_DOOR_STYLE = ItemStyle(color.brown, (1, 2.4, 1), 1.2, solid=True)


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
                texture=FLOOR_TEXTURE,
                texture_scale=(width, height),  # la texture se répète une fois par case
                color=color.white,
                collider="box",
            )
        )
        make_lit(
            Entity(
                model="plane",
                scale=(width, 1, height),
                position=cell_to_world(center_cell, self._wall_height),
                rotation_x=180,
                texture=CEILING_TEXTURE,
                texture_scale=(width, height),
                color=color.white,
            )
        )

    def _build_walls(self) -> None:
        for cell in self._level.wall_cells():
            make_lit(
                Entity(
                    model="cube",
                    position=cell_to_world(cell, self._wall_height / 2),
                    scale=(1, self._wall_height, 1),
                    texture=WALL_TEXTURE,
                    color=color.white,
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
        placements += [
            (cell, SECURITY_DOOR_STYLE) for cell in level.security_door_cells
        ]
        if level.keycard_cell is not None:
            placements.append((level.keycard_cell, KEYCARD_STYLE))
        for cell, style in placements:
            self._items[cell] = self._spawn_item(
                style, self._item_position(cell, style)
            )

    def _item_position(self, cell: Cell, style: ItemStyle) -> Vec3:
        """Sur son meuble s'il en a un (collé au mur), sinon au centre de la case."""
        wall_side = self._level.wall_side(cell)
        if style.support is None or wall_side is None:
            return cell_to_world(cell, style.height)
        top = place_furniture(cell, wall_side, style.support)
        return top + Vec3(0, style.scale[1] / 2, 0)  # posé, pas enfoncé

    @staticmethod
    def _spawn_item(style: ItemStyle, position: Vec3) -> Entity:
        return make_lit(
            Entity(
                model="cube",
                position=position,
                scale=style.scale,
                color=style.color,
                collider="box" if style.solid else None,
            )
        )
