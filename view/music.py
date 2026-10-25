"""Ambient music: a loop whose volume follows the moment of the game."""

from panda3d.core import Filename
from ursina import Entity, time

from core.paths import resource
from view.music_mix import MOODS, next_volume

MUSIC_PATH = resource("assets", "sounds", "music", "dread_theme.ogg")


class Music(Entity):
    """Plays the music in a loop. Ursina calls update() every frame: fades keep
    going on the title screen and during the intro, before the game even exists."""

    def __init__(self, app) -> None:
        super().__init__()
        self._volume = 0.0
        self._target = 0.0
        self._sound = None
        if not MUSIC_PATH.is_file():
            print(
                f"Warning: music not found ({MUSIC_PATH}). The game goes on without it."
            )
            return
        # Loaded as a sound effect: the menu's "Volume" setting applies to it too.
        self._sound = app.loader.loadSfx(
            Filename.fromOsSpecific(str(MUSIC_PATH.resolve()))
        )
        self._sound.setLoop(True)
        self._sound.setVolume(0.0)
        self._sound.play()

    def set_mood(self, mood: str) -> None:
        """ "title", "intro", "game", "chase" or "silent"."""
        self._target = MOODS[mood]

    def update(self) -> None:
        if self._sound is None:
            return
        self._volume = next_volume(self._volume, self._target, time.dt)
        self._sound.setVolume(self._volume)
