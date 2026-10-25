"""Sons du monstre : grognements, cri, pas, respirations."""

from panda3d.core import AudioSound

from view.sound_bank import SoundBank

GROWL_MIN_VOLUME = 0.08  # les grognements restent toujours audibles, faiblement
GROWL_INTERVAL = (4.0, 10.0)  # secondes entre deux grognements
BREATH_INTERVAL = (1.5, 3.5)  # secondes entre deux respirations
PATROL_STEP_INTERVAL = 0.9  # secondes entre deux pas lourds
CHASE_STEP_INTERVAL = 0.45  # secondes entre deux pas rapides


class MonsterSounds:
    """Joue le bon son selon l'état du monstre et sa proximité."""

    def __init__(self, bank: SoundBank) -> None:
        self._bank = bank
        self._growls = bank.load("monster", "monstre_grognement_*.ogg")
        self._short_steps = bank.load("monster", "monstre_pas_court_*.ogg")
        self._heavy_steps = bank.load("monster", "monstre_pas_lourd_*.ogg")
        self._breaths = bank.load("monster", "monstre_respiration_*.ogg")
        self._spotted = bank.load("monster", "monstre_cri.ogg")
        self._caught = bank.load("monster", "monstre_attrape.ogg")
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
        """Tous les sons du monstre, pour les accrocher à sa position dans l'espace."""
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
            self._current_growl.setVolume(volume)  # le grognement grossit s'il approche
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
