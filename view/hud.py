"""Interface affichée par-dessus le jeu. Ne contient aucune règle du jeu."""

from ursina import Entity, Text, camera, color, destroy

BAR_WIDTH = 0.3
BAR_HEIGHT = 0.018
BATTERY_POSITION = (-0.82, -0.44)
STAMINA_POSITION = (-0.82, -0.36)
LOW_BATTERY = 0.2

OBJECTIVE_POSITION = (-0.85, 0.46)
PROMPT_POSITION = (0, -0.3)
MESSAGE_POSITION = (0, -0.12)
MESSAGE_MIN_DURATION = 2.5  # secondes
READING_SPEED = 18  # caractères lus par seconde
READING_WRAP = 45  # nombre de caractères par ligne dans l'écran de lecture


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
    """Affiche ce que le joueur doit savoir."""

    def __init__(self) -> None:
        self._battery = GaugeBar("BATTERIE", BATTERY_POSITION, color.yellow, color.red)
        self._stamina = GaugeBar("ENDURANCE", STAMINA_POSITION, color.azure, color.gray)
        self._prompt = Text(
            "", parent=camera.ui, origin=(0, 0), position=PROMPT_POSITION
        )
        self._objective = Text(
            "",
            parent=camera.ui,
            origin=(-0.5, 0.5),
            position=OBJECTIVE_POSITION,
            scale=0.9,
            color=color.light_gray,
        )
        self._hiding_bars = [
            Entity(
                parent=camera.ui,
                model="quad",
                color=color.black,
                scale=(2, 0.36),
                y=y,
                z=0.5,
                enabled=False,
            )
            for y in (0.32, -0.32)
        ]

        self._reading_panel = Entity(
            parent=camera.ui,
            model="quad",
            color=color.black,
            scale=(1.2, 0.8),
            z=0.2,
            enabled=False,
        )
        self._reading_panel.alpha = 0.9
        self._reading_text = Text(
            "",
            parent=camera.ui,
            origin=(0, 0),
            y=0.03,
            enabled=False,
        )
        self._reading_hint = Text(
            "[E] Fermer",
            parent=camera.ui,
            origin=(0, 0),
            y=-0.33,
            color=color.light_gray,
            enabled=False,
        )

    def show_battery(self, ratio: float) -> None:
        self._battery.show(ratio, warning=ratio < LOW_BATTERY)

    def show_stamina(self, ratio: float, exhausted: bool) -> None:
        self._stamina.show(ratio, warning=exhausted)

    def show_prompt(self, text: str | None) -> None:
        self._prompt.text = f"[E] {text}" if text else ""

    def show_objective(self, text: str) -> None:
        label = f"OBJECTIF : {text}"
        if self._objective.text != label:
            self._objective.text = label

    def show_message(self, text: str) -> None:
        """Message temporaire. Plus il est long, plus il reste affiché."""
        duration = max(MESSAGE_MIN_DURATION, len(text) / READING_SPEED)
        message = Text(
            text,
            parent=camera.ui,
            origin=(0, 0),
            position=MESSAGE_POSITION,
            color=color.light_gray,
        )
        destroy(message, delay=duration)

    def show_hiding(self, hidden: bool) -> None:
        for bar in self._hiding_bars:
            bar.enabled = hidden

    def show_end(self, text: str, won: bool) -> None:
        self.show_prompt(None)
        self.show_hiding(False)
        Text(
            text,
            parent=camera.ui,
            origin=(0, 0),
            scale=2,
            color=color.lime if won else color.red,
        )
        Text(
            "Échap pour quitter",
            parent=camera.ui,
            origin=(0, 0),
            y=-0.1,
            color=color.light_gray,
        )

    @property
    def is_reading(self) -> bool:
        return self._reading_panel.enabled

    def show_document(self, text: str) -> None:
        self.show_prompt(None)
        self._reading_text.text = text
        self._reading_text.wordwrap = (
            READING_WRAP  # appliqué une fois le texte en place
        )
        for element in (self._reading_panel, self._reading_text, self._reading_hint):
            element.enabled = True

    def close_document(self) -> None:
        for element in (self._reading_panel, self._reading_text, self._reading_hint):
            element.enabled = False
