"""Interface affichée par-dessus le jeu : jauges de batterie et d'endurance."""

from ursina import Entity, Text, camera, color

BAR_WIDTH = 0.3
BAR_HEIGHT = 0.018
BATTERY_POSITION = (-0.82, -0.44)
STAMINA_POSITION = (-0.82, -0.36)
LOW_BATTERY = 0.2


class GaugeBar:
    """Une barre horizontale avec son titre, ancrée à l'écran."""

    def __init__(self, label: str, position: tuple, fill_color, warning_color) -> None:
        x, y = position
        self._fill_color = fill_color
        self._warning_color = warning_color
        Text(
            label,
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
            color=fill_color,
        )

    def show(self, ratio: float, warning: bool) -> None:
        self._fill.scale_x = BAR_WIDTH * ratio
        self._fill.color = self._warning_color if warning else self._fill_color


class Hud:
    """Affiche ce que le joueur doit savoir. Ne contient aucune règle du jeu."""

    def __init__(self) -> None:
        self._battery = GaugeBar("BATTERIE", BATTERY_POSITION, color.yellow, color.red)
        self._stamina = GaugeBar("ENDURANCE", STAMINA_POSITION, color.azure, color.gray)

    def show_battery(self, ratio: float) -> None:
        self._battery.show(ratio, warning=ratio < LOW_BATTERY)

    def show_stamina(self, ratio: float, exhausted: bool) -> None:
        self._stamina.show(ratio, warning=exhausted)
