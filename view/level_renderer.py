"""Construction du bâtiment en 3D à partir d'une FacilityMap.

Ce module affiche ; il ne contient aucune règle du jeu.
"""

import math
from dataclasses import dataclass

from panda3d.core import TransparencyAttrib
from ursina import Entity, Vec3, color, destroy

from core.level import Cell, FacilityMap
from view.abandon import scatter_debris, wall_textures
from view.coords import cell_to_world
from view.furniture import DESK, SHELF, FurnitureStyle, place_furniture
from view.lighting import make_lit
from view.model_loader import (
    EXIT_DOOR,
    GENERATOR,
    ModelLoadError,
    ModelSpec,
    place_model,
)

WALL_HEIGHT = 3.0
# Textures générées par tools/make_textures.py, rangées dans assets/textures/.
FLOOR_TEXTURE = "floor_tiles"
CEILING_TEXTURE = "ceiling_tiles"


@dataclass(frozen=True)
class ItemStyle:
    """Apparence provisoire d'un objet, en attendant de vrais modèles."""

    color: object
    scale: tuple[float, float, float]
    height: float
    solid: bool = False  # un objet solide bloque le joueur
    support: FurnitureStyle | None = None  # le meuble sur lequel l'objet est posé
    texture: str | None = None  # image de assets/textures/ ; sinon, la couleur seule
    model: ModelSpec | None = None  # modèle 3D ; sinon, un bloc texturé
    against_wall: bool = False  # adossé au mur le plus proche, face à la pièce


FUSE_STYLE = ItemStyle(
    color.yellow, (0.3, 0.12, 0.12), 1.0, support=SHELF, texture="fuse"
)
POWER_PANEL_STYLE = ItemStyle(
    color.azure, (0.9, 0.85, 0.9), 0.43, solid=True, model=GENERATOR
)
NOTE_STYLE = ItemStyle(
    color.white, (0.3, 0.02, 0.34), 0.9, support=DESK, texture="note"
)
BATTERY_STYLE = ItemStyle(
    color.orange, (0.15, 0.3, 0.15), 0.9, support=SHELF, texture="battery"
)
EXIT_STYLE = ItemStyle(
    color.green, (1.3, 2.3, 0.4), 1.15, model=EXIT_DOOR, against_wall=True
)
DOCUMENT_STYLE = ItemStyle(
    color.light_gray, (0.26, 0.02, 0.32), 0.9, support=DESK, texture="document"
)
LOCKER_STYLE = ItemStyle(
    color.dark_gray, (0.9, 2.2, 0.9), 1.1, solid=True, texture="locker"
)
KEYCARD_STYLE = ItemStyle(
    color.cyan, (0.3, 0.02, 0.22), 0.9, support=DESK, texture="keycard"
)
SECURITY_DOOR_STYLE = ItemStyle(
    color.brown, (1, 2.4, 1), 1.2, solid=True, texture="security_door"
)
DOOR_SIZE = (1.0, 2.4, 0.08)  # largeur, hauteur, épaisseur du battant
DOOR_TEXTURE = "door"
DEBRIS_HEIGHT = 0.01  # juste au-dessus du sol
DEBRIS_LAYER = 0.0005
DOOR_OPEN_ANGLE = 95  # degrés : la porte ouverte se rabat presque contre le mur


class LevelRenderer:
    """Construit les murs, le sol, le plafond et les objets d'un niveau."""

    def __init__(
        self, level: FacilityMap, wall_height: float = WALL_HEIGHT, app=None
    ) -> None:
        self._level = level
        self._app = app  # sans application, pas de modèles 3D : des blocs de couleur
        self._wall_height = wall_height
        self._items: dict[Cell, Entity] = {}
        self._doors: dict[Cell, tuple[Entity, Entity]] = {}  # (gond, battant)

    def build(self) -> None:
        self._build_floor_and_ceiling()
        self._build_walls()
        self._build_debris()
        self._build_items()
        self._build_doors()

    def sync_doors(self, doors) -> list[Cell]:
        """Ouvre ou ferme les portes affichées comme dans le noyau.

        Renvoie les cases des portes qui ont bougé, pour jouer un bruit.
        """
        moved = []
        for door in doors:
            hinge, panel = self._doors[door.cell]
            is_open = not door.is_closed
            if (hinge.rotation_y != 0) == is_open:
                continue
            hinge.rotation_y = DOOR_OPEN_ANGLE if is_open else 0
            panel.collider = None if is_open else "box"
            moved.append(door.cell)
        return moved

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
        textures = wall_textures(self._level)  # fissures, humidité, trous, griffures
        for cell in self._level.wall_cells():
            make_lit(
                Entity(
                    model="cube",
                    position=cell_to_world(cell, self._wall_height / 2),
                    scale=(1, self._wall_height, 1),
                    texture=textures[cell],
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
            if style.model is not None and self._app is not None:
                self._items[cell] = self._spawn_model(cell, style)
            else:
                self._items[cell] = self._spawn_item(
                    style, self._item_position(cell, style)
                )

    def _spawn_model(self, cell: Cell, style: ItemStyle) -> Entity:
        """Un modèle 3D, tourné vers la pièce ; un bloc de couleur s'il manque."""
        holder = Entity(position=cell_to_world(cell))
        wall_side = self._level.wall_side(cell) if style.against_wall else None
        if wall_side is not None:
            d_row, d_col = wall_side
            depth = style.scale[2]
            holder.position += Vec3(d_col, 0, -d_row) * (0.5 - depth / 2)
            holder.rotation_y = math.degrees(math.atan2(-d_col, d_row))  # dos au mur
        try:
            place_model(self._app, style.model, holder)
        except ModelLoadError as error:
            print(f"{error} Un bloc de couleur le remplace.")
            destroy(holder)
            return self._spawn_item(style, self._item_position(cell, style))
        if style.solid:
            Entity(
                parent=holder,
                model="cube",
                y=style.scale[1] / 2,
                scale=style.scale,
                collider="box",
                visible=False,
            )
        return holder

    def _build_debris(self) -> None:
        """Papiers, gravats, éclats de carrelage et taches, posés à plat sur le sol."""
        for index, debris in enumerate(scatter_debris(self._level)):
            dx, dz = debris.offset
            height = DEBRIS_HEIGHT + index * DEBRIS_LAYER  # évite qu'ils se chevauchent
            decal = make_lit(
                Entity(
                    model="quad",
                    texture=debris.texture,
                    position=cell_to_world(debris.cell, height) + Vec3(dx, 0, dz),
                    rotation=(90, debris.angle, 0),
                    scale=debris.size,
                    double_sided=True,
                )
            )
            decal.setTransparency(TransparencyAttrib.MAlpha)

    def _build_doors(self) -> None:
        """Chaque battant tourne autour d'un gond posé contre le mur."""
        for cell in self._level.door_cells:
            row, col = cell
            across_columns = self._level.is_wall(
                (row, col - 1)
            )  # murs à gauche et à droite
            frame = Entity(
                position=cell_to_world(cell), rotation_y=0 if across_columns else 90
            )
            hinge = Entity(parent=frame, x=-DOOR_SIZE[0] / 2)
            width, height, _ = DOOR_SIZE
            panel = make_lit(
                Entity(
                    parent=hinge,
                    model="cube",
                    position=(width / 2, height / 2, 0),
                    scale=DOOR_SIZE,
                    texture=DOOR_TEXTURE,
                    collider="box",
                )
            )
            self._doors[cell] = (hinge, panel)

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
                texture=style.texture,
                color=color.white if style.texture else style.color,
                collider="box" if style.solid else None,
            )
        )
