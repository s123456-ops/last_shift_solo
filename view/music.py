"""La musique d'ambiance : une boucle dont le volume suit le moment de la partie."""

from pathlib import Path

from panda3d.core import Filename
from ursina import Entity, time

from view.music_mix import MOODS, next_volume

MUSIC_PATH = Path("assets/sounds/music/musique_menace.ogg")


class Music(Entity):
    """Joue la musique en boucle. Ursina appelle update() à chaque image : les fondus
    continuent sur l'écran titre et pendant l'intro, avant même que la partie existe."""

    def __init__(self, app) -> None:
        super().__init__()
        self._volume = 0.0
        self._target = 0.0
        self._sound = None
        if not MUSIC_PATH.is_file():
            print(
                f"Avertissement : musique introuvable ({MUSIC_PATH}). Le jeu continue sans."
            )
            return
        # Chargée comme un effet sonore : le réglage « Volume » du menu s'applique aussi.
        self._sound = app.loader.loadSfx(
            Filename.fromOsSpecific(str(MUSIC_PATH.resolve()))
        )
        self._sound.setLoop(True)
        self._sound.setVolume(0.0)
        self._sound.play()

    def set_mood(self, mood: str) -> None:
        """« title », « intro », « game », « chase » ou « silent »."""
        self._target = MOODS[mood]

    def update(self) -> None:
        if self._sound is None:
            return
        self._volume = next_volume(self._volume, self._target, time.dt)
        self._sound.setVolume(self._volume)
