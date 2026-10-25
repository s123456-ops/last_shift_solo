"""Gouttes d'eau près des murs humides : le son confirme ce que l'image montre."""

from panda3d.core import AudioSound
from ursina import Entity, Vec3, camera

from view.sound_bank import SoundBank

DRIP_RANGE = 9.0  # mètres : au-delà, on n'entend plus les gouttes
DRIP_VOLUME = 0.45
DRIP_INTERVAL = (1.2, 3.5)  # secondes entre deux gouttes


class DripSounds:
    """Fait tomber une goutte, de temps en temps, près d'un mur humide proche."""

    def __init__(self, bank: SoundBank, audio3d, points: list[Vec3]) -> None:
        self._bank = bank
        self._points = points
        self._sounds: list[AudioSound] = bank.load("ambiance", "goutte_*.wav")
        self._emitter = Entity()  # l'endroit d'où part la goutte
        for sound in self._sounds:
            audio3d.attachSoundToObject(sound, self._emitter)
        self._timer = bank.rng.uniform(*DRIP_INTERVAL)

    def update(self, dt: float) -> None:
        self._timer -= dt
        if self._timer > 0:
            return
        self._timer = self._bank.rng.uniform(*DRIP_INTERVAL)
        listener = camera.world_position
        nearby = [p for p in self._points if (p - listener).length() < DRIP_RANGE]
        if not nearby:
            return
        point = self._bank.rng.choice(nearby)
        self._emitter.position = point
        distance = (point - listener).length()
        self._bank.play(self._sounds, DRIP_VOLUME * (1 - distance / DRIP_RANGE) ** 2)
