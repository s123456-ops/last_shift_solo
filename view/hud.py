"""Interface affichée par-dessus le jeu : jauge de batterie."""

from ursina import Entity, Text, camera, color

BAR_POSITION = (-0.82, -0.44)
BAR_WIDTH = 0.3
BAR_HEIGHT = 0.018
LOW_BATTERY = 0.2  # en dessous de 20 %, la jauge passe au rouge


class Hud:
    """Affiche ce que le joueur doit savoir. Ne contient aucune règle du jeu."""

    def __init__(self) -> None:
        x, y = BAR_POSITION
        Text(
            "BATTERIE",
            parent=camera.ui,
            position=(x, y + 0.04),
            scale=0.8,
            color=color.light_gray,
        )
        Entity(
            parent=camera.ui,
            model="quad",
            origin=(-0.5, 0),
            position=(x, y, 0),
            scale=(BAR_WIDTH, BAR_HEIGHT),
            color=color.dark_gray,
        )
        self._fill = Entity(
            parent=camera.ui,
            model="quad",
            origin=(-0.5, 0),
            position=(x, y, -0.01),
            scale=(BAR_WIDTH, BAR_HEIGHT),
            color=color.yellow,
        )

    def show_battery(self, ratio: float) -> None:
        self._fill.scale_x = BAR_WIDTH * ratio
        self._fill.color = color.red if ratio < LOW_BATTERY else color.yellow
