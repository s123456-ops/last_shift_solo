"""Le plan du bâtiment, ouvert avec la touche M. Ne contient aucune règle du jeu."""

from ursina import Entity, Text, Texture, Vec3, camera, color

from core.difficulty import Difficulty
from core.level import FacilityMap
from core.texts import tr
from view.coords import world_to_grid
from view.plan_image import draw_plan, landmarks

PLAN_HEIGHT = 0.62  # hauteur du plan à l'écran (l'écran fait 1 de haut)
PLAN_Y = 0.04
MARKER_SIZE = 1.6  # taille d'un repère, en cases
PLAYER_SIZE = 1.3
LEGEND_SPACING = 0.27
BACKGROUND_OPACITY = 0.88


class MapScreen:
    """Affiche le plan, ses repères, sa légende et la position du joueur."""

    def __init__(self, level: FacilityMap, difficulty: Difficulty) -> None:
        self._level = level
        self._marks = landmarks(level, show_keycard=difficulty.plan_shows_keycard)
        self._shows_player = difficulty.plan_shows_player
        self._root = Entity(parent=camera.ui, enabled=False)
        background = Entity(
            parent=self._root, model="quad", color=color.black, scale=(2, 1), z=0.3
        )
        background.alpha = BACKGROUND_OPACITY
        width = PLAN_HEIGHT * level.width / level.height
        self._plan = Entity(
            parent=self._root,
            model="quad",
            texture=Texture(draw_plan(level)),
            scale=(width, PLAN_HEIGHT),
            y=PLAN_Y,
            z=0.2,
        )
        self._plan.texture.filtering = None  # pixels nets, pas de flou
        self._cell_size = PLAN_HEIGHT / level.height
        self._build_landmarks()
        self._player = Entity(
            parent=self._root,
            model="circle",
            color=color.red,
            scale=self._cell_size * PLAYER_SIZE,
            z=0.05,
            enabled=self._shows_player,
        )
        self._build_texts()

    @property
    def is_open(self) -> bool:
        return self._root.enabled

    def toggle(self) -> None:
        self._root.enabled = not self._root.enabled

    def close(self) -> None:
        self._root.enabled = False

    def show_player(self, position: Vec3) -> None:
        """Place le point rouge là où se trouve le joueur, sans arrondir à la case."""
        row, col = world_to_grid(position)
        self._player.x, self._player.y = self._to_screen(row, col)

    def _to_screen(self, row: float, col: float) -> tuple[float, float]:
        """Ligne et colonne de la carte → position à l'écran, sur le plan."""
        x = self._plan.x + ((col + 0.5) / self._level.width - 0.5) * self._plan.scale_x
        y = self._plan.y + (0.5 - (row + 0.5) / self._level.height) * PLAN_HEIGHT
        return x, y

    def _build_landmarks(self) -> None:
        for mark in self._marks:
            x, y = self._to_screen(*mark.cell)
            Entity(
                parent=self._root,
                model="quad",
                color=color.rgb32(*mark.rgb),
                scale=self._cell_size * MARKER_SIZE,
                position=(x, y, 0.1),
            )

    def _build_texts(self) -> None:
        top = PLAN_Y + PLAN_HEIGHT / 2
        bottom = PLAN_Y - PLAN_HEIGHT / 2
        Text(tr("map.title"), parent=self._root, origin=(0, 0), y=top + 0.05)
        Text(
            tr("map.hint"),
            parent=self._root,
            origin=(0, 0),
            y=bottom - 0.12,
            color=color.light_gray,
        )
        legend = {mark.label_key: mark.rgb for mark in self._marks}
        entries = [(tr(key), color.rgb32(*rgb)) for key, rgb in legend.items()]
        if self._shows_player:
            entries.append((tr("map.you"), color.red))
        start = -LEGEND_SPACING * (len(entries) - 1) / 2
        for index, (label, swatch) in enumerate(entries):
            x = start + index * LEGEND_SPACING
            Entity(
                parent=self._root,
                model="quad",
                color=swatch,
                scale=0.018,
                position=(x - 0.1, bottom - 0.05, 0.1),
            )
            Text(
                label,
                parent=self._root,
                origin=(-0.5, 0),
                position=(x - 0.08, bottom - 0.05),
                scale=0.75,
                color=color.light_gray,
            )
