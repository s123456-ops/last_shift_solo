"""Ambiance du bâtiment : néon, bruits lointains, courant rétabli."""
from view.sound_bank import LoopChannel, SoundBank

NEON_VOLUME = 0.15               # à peine audible : on ne le remarque que s'il s'arrête
NEON_POWER_BOOST = 1.6           # les néons se rallument quand le courant revient
NEON_DUCKING = 0.8               # il s'efface de 80 % quand le monstre est tout près
NEON_HIDDEN_FACTOR = 0.2         # dans un casier, le monde se tait
DISTANT_INTERVAL = (30.0, 60.0)  # secondes entre deux bruits lointains
DISTANT_VOLUME = 0.3
POWER_ON_VOLUME = 0.8


class AmbienceSounds:
    """Le fond sonore du bâtiment, toujours discret."""

    def __init__(self, bank: SoundBank) -> None:
        self._bank = bank
        self._neon = LoopChannel(bank.load_one("ambiance", "ambiance_neon.ogg"), fade_speed=1.0)
        self._distant = bank.load("ambiance", "bruit_lointain_*.ogg")
        self._power_on = bank.load("ambiance", "courant_retabli.ogg")
        self._distant_timer = bank.rng.uniform(*DISTANT_INTERVAL)

    def update(self, dt: float, closeness: float, chasing: bool, hidden: bool,
               power_on: bool) -> None:
        volume = NEON_VOLUME
        volume *= NEON_POWER_BOOST if power_on else 1.0
        volume *= 1.0 - NEON_DUCKING * closeness
        volume *= NEON_HIDDEN_FACTOR if hidden else 1.0
        self._neon.set(volume)
        self._neon.update(dt)
        if chasing:
            return   # jamais de bruit lointain pendant une poursuite
        self._distant_timer -= dt
        if self._distant_timer <= 0:
            self._bank.play(self._distant, DISTANT_VOLUME)
            self._distant_timer = self._bank.rng.uniform(*DISTANT_INTERVAL)

    def on_power_restored(self) -> None:
        self._bank.play(self._power_on, POWER_ON_VOLUME)

    def stop_all(self) -> None:
        self._neon.stop()