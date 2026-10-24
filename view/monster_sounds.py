"""Sons du monstre : grognements, cri, pas, respirations.

Les sons sont chargés avec le chargeur audio de Panda3D, comme les modèles 3D.
Ce module affiche des informations, il ne décide jamais rien.
"""

import random
from pathlib import Path

from panda3d.core import AudioSound, Filename

SOUND_DIR = Path("assets/sounds/monster")
HEARING_DISTANCE = 18.0  # au-delà, on n'entend plus ses pas (en mètres)
GROWL_MIN_VOLUME = 0.08  # les grognements restent toujours audibles, faiblement
GROWL_INTERVAL = (4.0, 10.0)  # secondes entre deux grognements
BREATH_INTERVAL = (1.5, 3.5)  # secondes entre deux respirations
PATROL_STEP_INTERVAL = 0.9  # secondes entre deux pas lourds
CHASE_STEP_INTERVAL = 0.45  # secondes entre deux pas rapides


class MonsterSounds:
    """Joue le bon son selon l'état du monstre et sa distance au joueur."""

    def __init__(self, app, rng: random.Random | None = None) -> None:
        self._app = app
        self._rng = rng or random.Random()
        self._growls = self._load("monstre_grognement_*.ogg")
        self._short_steps = self._load("monstre_pas_court_*.ogg")
        self._heavy_steps = self._load("monstre_pas_lourd_*.ogg")
        self._breaths = self._load("monstre_respiration_*.ogg")
        self._spotted = self._load("monstre_cri.ogg")
        self._caught = self._load("monstre_attrape.ogg")
        self._current_growl: AudioSound | None = None
        self._growl_timer = self._rng.uniform(*GROWL_INTERVAL)
        self._breath_timer = self._rng.uniform(*BREATH_INTERVAL)
        self._was_chasing = False
        self._step_timer = 0.0

    def update(
        self, dt: float, distance: float, chasing: bool, searching: bool
    ) -> None:
        """Appelée à chaque image."""
        closeness = self._closeness(distance)
        if chasing and not self._was_chasing:
            self._play(self._spotted, max(0.6, closeness))
        self._was_chasing = chasing
        self._update_steps(dt, closeness, chasing)
        self._update_growls(dt, closeness, patrolling=not chasing and not searching)
        if searching:
            self._update_breaths(dt, closeness)

    def _update_steps(self, dt: float, closeness: float, chasing: bool) -> None:
        """Un pas à intervalle régulier, plus rapproché quand il poursuit."""
        self._step_timer -= dt
        if self._step_timer > 0:
            return
        if closeness > 0:
            self._play(self._short_steps if chasing else self._heavy_steps, closeness)
        self._step_timer = CHASE_STEP_INTERVAL if chasing else PATROL_STEP_INTERVAL

    def on_caught(self) -> None:
        self.stop_all()
        self._play(self._caught, 1.0)

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

    def _update_growls(self, dt: float, closeness: float, patrolling: bool) -> None:
        volume = GROWL_MIN_VOLUME + (1 - GROWL_MIN_VOLUME) * closeness
        if self._current_growl is not None and self._is_playing(self._current_growl):
            self._current_growl.setVolume(volume)  # le grognement grossit s'il approche
            return
        if not patrolling:
            return
        self._growl_timer -= dt
        if self._growl_timer <= 0:
            self._current_growl = self._play(self._growls, volume)
            self._growl_timer = self._rng.uniform(*GROWL_INTERVAL)

    def _update_breaths(self, dt: float, closeness: float) -> None:
        self._breath_timer -= dt
        if self._breath_timer <= 0:
            self._play(self._breaths, closeness)
            self._breath_timer = self._rng.uniform(*BREATH_INTERVAL)

    @staticmethod
    def _closeness(distance: float) -> float:
        """1 tout près, 0 au-delà de la distance d'audition, décroissance douce entre les deux."""
        linear = max(0.0, 1.0 - distance / HEARING_DISTANCE)
        return linear * linear

    def _play(self, sounds: list[AudioSound], volume: float) -> AudioSound | None:
        if not sounds or volume <= 0:
            return None
        sound = self._rng.choice(sounds)
        sound.setVolume(volume)
        sound.play()
        return sound

    @staticmethod
    def _is_playing(sound: AudioSound) -> bool:
        return sound.status() == AudioSound.PLAYING

    def _load(self, pattern: str) -> list[AudioSound]:
        paths = sorted(SOUND_DIR.glob(pattern))
        if not paths:
            print(
                f"Avertissement : aucun son « {pattern} » dans {SOUND_DIR}. Le jeu continue sans."
            )
        return [
            self._app.loader.loadSfx(Filename.fromOsSpecific(str(path.resolve())))
            for path in paths
        ]
