"""Monster sounds: growls, scream, footsteps, breathing."""

from panda3d.core import AudioSound

from view.sound_bank import SoundBank

GROWL_MIN_VOLUME = 0.08  # growls always stay faintly audible
GROWL_INTERVAL = (4.0, 10.0)  # seconds between two growls
BREATH_INTERVAL = (1.5, 3.5)  # seconds between two breaths
PATROL_STEP_INTERVAL = 0.9  # seconds between two heavy footsteps
CHASE_STEP_INTERVAL = 0.45  # seconds between two fast footsteps


class MonsterSounds:
    """Plays the right sound for the monster's state and distance."""

    def __init__(self, bank: SoundBank) -> None:
        self._bank = bank
        self._growls = bank.load("monster", "monster_growl_*.ogg")
        self._short_steps = bank.load("monster", "monster_step_fast_*.ogg")
        self._heavy_steps = bank.load("monster", "monster_step_heavy_*.ogg")
        self._breaths = bank.load("monster", "monster_breath_*.ogg")
        self._spotted = bank.load("monster", "monster_scream.ogg")
        self._caught = bank.load("monster", "monster_caught.ogg")
        self._current_growl: AudioSound | None = None
        self._growl_timer = bank.rng.uniform(*GROWL_INTERVAL)
        self._breath_timer = bank.rng.uniform(*BREATH_INTERVAL)
        self._step_timer = 0.0
        self._was_chasing = False

    def update(
        self, dt: float, closeness: float, chasing: bool, searching: bool
    ) -> None:
        if chasing and not self._was_chasing:
            self._bank.play(self._spotted, max(0.6, closeness))
        self._was_chasing = chasing
        self._update_steps(dt, closeness, chasing)
        self._update_growls(dt, closeness, patrolling=not chasing and not searching)
        if searching:
            self._update_breaths(dt, closeness)

    def sounds(self) -> list[AudioSound]:
        """All the monster's sounds, to attach them to its position in space."""
        return [
            *self._growls,
            *self._short_steps,
            *self._heavy_steps,
            *self._breaths,
            *self._spotted,
            *self._caught,
        ]

    def on_caught(self) -> None:
        self.stop_all()
        self._bank.play(self._caught, 1.0)

    def stop_all(self) -> None:
        for group in (
            self._growls,
            self._short_steps,
            self._heavy_steps,
            self._breaths,
            self._spotted,
        ):
            for sound in group:
                sound.stop()

    def _update_steps(self, dt: float, closeness: float, chasing: bool) -> None:
        self._step_timer -= dt
        if self._step_timer > 0:
            return
        if closeness > 0:
            self._bank.play(
                self._short_steps if chasing else self._heavy_steps, closeness
            )
        self._step_timer = CHASE_STEP_INTERVAL if chasing else PATROL_STEP_INTERVAL

    def _update_growls(self, dt: float, closeness: float, patrolling: bool) -> None:
        volume = GROWL_MIN_VOLUME + (1 - GROWL_MIN_VOLUME) * closeness
        if self._bank.is_playing(self._current_growl):
            self._current_growl.setVolume(
                volume
            )  # the growl gets louder as it comes closer
            return
        if not patrolling:
            return
        self._growl_timer -= dt
        if self._growl_timer <= 0:
            self._current_growl = self._bank.play(self._growls, volume)
            self._growl_timer = self._bank.rng.uniform(*GROWL_INTERVAL)

    def _update_breaths(self, dt: float, closeness: float) -> None:
        self._breath_timer -= dt
        if self._breath_timer <= 0:
            self._bank.play(self._breaths, closeness)
            self._breath_timer = self._bank.rng.uniform(*BREATH_INTERVAL)
