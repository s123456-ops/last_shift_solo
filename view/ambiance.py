"""Building ambience: neon hum, distant noises, power restored."""

from view.sound_bank import LoopChannel, SoundBank

NEON_VOLUME = 0.15  # barely audible: you only notice it when it stops
NEON_POWER_BOOST = 1.6  # the neon lights come back on with the power
NEON_DUCKING = 0.8  # it fades by 80 % when the monster is right there
NEON_HIDDEN_FACTOR = 0.2  # inside a locker, the world goes quiet
DISTANT_INTERVAL = (30.0, 60.0)  # seconds between two distant noises
DISTANT_VOLUME = 0.3
POWER_ON_VOLUME = 0.8


class AmbienceSounds:
    """The building's background sound, always discreet."""

    def __init__(self, bank: SoundBank) -> None:
        self._bank = bank
        self._neon = LoopChannel(
            bank.load_one("ambiance", "neon_hum.ogg"), fade_speed=1.0
        )
        self._distant = bank.load("ambiance", "distant_noise_*.ogg")
        self._power_on = bank.load("ambiance", "power_restored.ogg")
        self._distant_timer = bank.rng.uniform(*DISTANT_INTERVAL)

    def update(
        self, dt: float, closeness: float, chasing: bool, hidden: bool, power_on: bool
    ) -> None:
        volume = NEON_VOLUME
        volume *= NEON_POWER_BOOST if power_on else 1.0
        volume *= 1.0 - NEON_DUCKING * closeness
        volume *= NEON_HIDDEN_FACTOR if hidden else 1.0
        self._neon.set(volume)
        self._neon.update(dt)
        if chasing:
            return  # never a distant noise during a chase
        self._distant_timer -= dt
        if self._distant_timer <= 0:
            self._bank.play(self._distant, DISTANT_VOLUME)
            self._distant_timer = self._bank.rng.uniform(*DISTANT_INTERVAL)

    def on_power_restored(self) -> None:
        self._bank.play(self._power_on, POWER_ON_VOLUME)

    def stop_all(self) -> None:
        self._neon.stop()
