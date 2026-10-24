"""Écrans hors partie : titre et introduction."""

from collections.abc import Callable

from ursina import (
    Button,
    Entity,
    Text,
    application,
    camera,
    color,
    destroy,
    mouse,
    time,
)

from core.texts import tr

INTRO_CARD_KEYS = ("intro.1", "intro.2", "intro.3", "intro.4")
FADE_DURATION = 1.0  # secondes d'apparition et de disparition de chaque carton
HOLD_DURATION = 3.0  # secondes où le carton reste pleinement affiché
SKIP_KEYS = ("space", "enter")
TITLE_BAND_OPACITY = 0.55


class TitleScreen(Entity):
    """Titre du jeu, avec Commencer et Quitter, par-dessus le décor."""

    def __init__(self, on_start: Callable[[], None]) -> None:
        super().__init__(parent=camera.ui)
        self._on_start = on_start
        mouse.locked = False
        mouse.visible = True
        band = Entity(
            parent=self, model="quad", color=color.black, scale=(2, 0.62), y=0.02, z=0.1
        )
        band.alpha = TITLE_BAND_OPACITY
        Text(
            "THE LAST SHIFT",
            parent=self,
            origin=(0, 0),
            y=0.18,
            scale=4,
            color=color.light_gray,
        )
        Text(tr("title.subtitle"), parent=self, origin=(0, 0), y=0.06, color=color.gray)
        buttons = (
            (tr("title.start"), -0.08, self._start),
            (tr("title.quit"), -0.18, application.quit),
        )
        for label, y, action in buttons:
            Button(
                label,
                parent=self,
                y=y,
                scale=(0.3, 0.07),
                color=color.black,
                highlight_color=color.dark_gray,
                text_color=color.light_gray,
                on_click=action,
            )

    def _start(self) -> None:
        on_start = self._on_start
        destroy(self)
        on_start()


class IntroSequence(Entity):
    """Les cartons de l'intro, en fondu sur fond noir, passables à tout moment."""

    def __init__(self, on_finish: Callable[[], None]) -> None:
        super().__init__()
        self._on_finish = on_finish
        self._finished = False
        self._background = Entity(
            parent=camera.ui,
            model="quad",
            color=color.black,
            scale=(3, 2),
            z=1,
        )
        self._card = Text("", parent=camera.ui, origin=(0, 0), color=color.light_gray)
        self._hint = Text(
            tr("intro.skip"),
            parent=camera.ui,
            origin=(0, 0),
            y=-0.42,
            scale=0.8,
            color=color.dark_gray,
        )
        self._index = -1
        self._elapsed = 0.0
        self._next_card()

    def update(self) -> None:
        if self._finished:
            return
        self._elapsed += time.dt
        card_duration = 2 * FADE_DURATION + HOLD_DURATION
        if self._elapsed >= card_duration:
            self._next_card()
            return
        fade_in = self._elapsed / FADE_DURATION
        fade_out = (card_duration - self._elapsed) / FADE_DURATION
        self._card.alpha = max(0.0, min(1.0, fade_in, fade_out))

    def input(self, key: str) -> None:
        if key in SKIP_KEYS:
            self._finish()

    def _next_card(self) -> None:
        self._index += 1
        if self._index >= len(INTRO_CARD_KEYS):
            self._finish()
            return
        self._card.text = tr(INTRO_CARD_KEYS[self._index])
        self._card.alpha = 0.0
        self._elapsed = 0.0

    def _finish(self) -> None:
        if self._finished:
            return
        self._finished = True
        on_finish = self._on_finish  # on la garde avant de détruire l'objet
        for element in (self._background, self._card, self._hint):
            destroy(element)
        destroy(self)
        on_finish()
