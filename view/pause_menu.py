"""Le menu pause : reprendre, régler les options, quitter. Aucune règle du jeu ici."""

from collections.abc import Callable

from ursina import Button, Entity, Text, camera, color

from core.texts import tr
from view.settings import PlayerSettings, Setting

BUTTON_SCALE = (0.46, 0.065)
BUTTON_SPACING = 0.085
FIRST_BUTTON_Y = 0.12
BACKGROUND_OPACITY = 0.8


class PauseMenu:
    """Un écran assombri avec des boutons. Les réglages s'appliquent immédiatement."""

    def __init__(
        self,
        settings: PlayerSettings,
        on_resume: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._root = Entity(parent=camera.ui, enabled=False)
        background = Entity(
            parent=self._root, model="quad", color=color.black, scale=(2, 1), z=0.2
        )
        background.alpha = BACKGROUND_OPACITY
        Text(tr("pause.title"), parent=self._root, origin=(0, 0), y=0.27, scale=2)
        self._make_button(tr("pause.resume"), 0, on_resume)
        self._setting_buttons: list[tuple[Button, Setting]] = []
        for index, setting in enumerate(settings.all(), start=1):
            button = self._make_button(
                setting.label, index, lambda chosen=setting: self._cycle(chosen)
            )
            self._setting_buttons.append((button, setting))
        self._make_button(tr("title.quit"), len(settings.all()) + 1, on_quit)
        Text(
            tr("pause.hint"),
            parent=self._root,
            origin=(0, 0),
            y=FIRST_BUTTON_Y - BUTTON_SPACING * (len(settings.all()) + 2.2),
            scale=0.8,
            color=color.light_gray,
        )

    def show(self, visible: bool) -> None:
        self._root.enabled = visible

    def _make_button(self, label: str, row: int, action: Callable[[], None]) -> Button:
        return Button(
            label,
            parent=self._root,
            y=FIRST_BUTTON_Y - row * BUTTON_SPACING,
            scale=BUTTON_SCALE,
            color=color.black,
            highlight_color=color.dark_gray,
            text_color=color.light_gray,
            on_click=action,
        )

    def _cycle(self, setting: Setting) -> None:
        setting.next()
        for button, shown in self._setting_buttons:
            button.text = shown.label
