"""Façade audio : le contrôleur ne parle qu'à cette classe."""

from dataclasses import dataclass

from view.ambiance import AmbienceSounds
from view.monster_sounds import MonsterSounds
from view.player_sounds import PlayerSounds
from view.sound_bank import SoundBank, closeness


@dataclass(frozen=True)
class AudioState:
    """Ce que le son doit savoir de la partie, à chaque image."""

    monster_distance: float
    monster_active: bool
    monster_chasing: bool
    monster_searching: bool
    player_moving: bool
    player_running: bool
    player_exhausted: bool
    player_hidden: bool
    power_on: bool


class GameAudio:
    """Coordonne les sons du monstre, du joueur et de l'ambiance."""

    def __init__(self, app) -> None:
        bank = SoundBank(app)
        self._monster = MonsterSounds(bank)
        self._player = PlayerSounds(bank)
        self._ambience = AmbienceSounds(bank)
        self._power_was_on = False

    def update(self, dt: float, state: AudioState) -> None:
        near = closeness(state.monster_distance) if state.monster_active else 0.0
        chasing = state.monster_active and state.monster_chasing
        if state.monster_active:
            self._monster.update(dt, near, chasing, state.monster_searching)
        self._player.update(
            dt,
            state.player_moving,
            state.player_running,
            state.player_exhausted,
            near,
            chasing,
        )
        self._ambience.update(dt, near, chasing, state.player_hidden, state.power_on)
        if state.power_on and not self._power_was_on:
            self._ambience.on_power_restored()
        self._power_was_on = state.power_on

    def on_flashlight(self, on: bool) -> None:
        self._player.on_flashlight(on)

    def on_pickup(self) -> None:
        self._player.on_pickup()

    def on_locker(self) -> None:
        self._player.on_locker()

    def on_won(self) -> None:
        self._stop_everything()

    def on_caught(self) -> None:
        self._stop_everything()
        self._monster.on_caught()

    def _stop_everything(self) -> None:
        self._monster.stop_all()
        self._player.stop_all()
        self._ambience.stop_all()
