"""Shared audio toolbox: loading, playing, loops and closeness."""

import random

from panda3d.core import AudioSound, Filename

from core.paths import resource

SOUNDS_ROOT = resource("assets", "sounds")
HEARING_DISTANCE = 18.0  # beyond this, the monster counts as far away (in metres)


def closeness(distance: float) -> float:
    """1 when right there, 0 beyond HEARING_DISTANCE, with a smooth rise."""
    linear = max(0.0, 1.0 - distance / HEARING_DISTANCE)
    return linear * linear


class SoundBank:
    """Loads sounds from assets/sounds and plays them."""

    def __init__(self, app, rng: random.Random | None = None) -> None:
        self._app = app
        self._rng = rng or random.Random()

    @property
    def rng(self) -> random.Random:
        return self._rng

    def load(self, folder: str, pattern: str) -> list[AudioSound]:
        """Every file in a folder that matches the pattern; an empty list otherwise."""
        directory = SOUNDS_ROOT / folder
        paths = sorted(directory.glob(pattern))
        if not paths:
            print(
                f"Warning: no sound '{pattern}' in {directory}. The game goes on without it."
            )
        return [
            self._app.loader.loadSfx(Filename.fromOsSpecific(str(path.resolve())))
            for path in paths
        ]

    def load_one(self, folder: str, name: str) -> AudioSound | None:
        sounds = self.load(folder, name)
        return sounds[0] if sounds else None

    def play(self, sounds: list[AudioSound], volume: float) -> AudioSound | None:
        """Plays a sound picked at random from the list."""
        if not sounds or volume <= 0:
            return None
        sound = self._rng.choice(sounds)
        sound.setVolume(min(volume, 1.0))
        sound.play()
        return sound

    @staticmethod
    def is_playing(sound: AudioSound | None) -> bool:
        return sound is not None and sound.status() == AudioSound.PLAYING


class LoopChannel:
    """A permanently looping sound whose volume slides smoothly towards a target."""

    def __init__(self, sound: AudioSound | None, fade_speed: float = 2.0) -> None:
        self._sound = sound
        self._fade_speed = fade_speed
        self._volume = 0.0
        self._target = 0.0
        if sound is not None:
            sound.setLoop(True)
            sound.setVolume(0.0)
            sound.play()

    def set(self, volume: float, rate: float = 1.0) -> None:
        self._target = min(volume, 1.0)
        if self._sound is not None:
            self._sound.setPlayRate(rate)

    def update(self, dt: float) -> None:
        if self._sound is None:
            return
        self._volume += (self._target - self._volume) * min(1.0, dt * self._fade_speed)
        self._sound.setVolume(self._volume)

    def stop(self) -> None:
        if self._sound is not None:
            self._sound.stop()
