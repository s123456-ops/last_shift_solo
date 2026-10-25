"""Audio facade: the controller only talks to this class."""

from dataclasses import dataclass

from direct.showbase.Audio3DManager import Audio3DManager
from ursina import Entity, Vec3, camera

from view.ambiance import AmbienceSounds
from view.drips import DripSounds
from view.monster_sounds import MonsterSounds
from view.player_sounds import PlayerSounds
from view.sound_bank import SoundBank, closeness


@dataclass(frozen=True)
class AudioState:
    """What the sound needs to know about the game, every frame."""

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
    """Coordinates the monster, player and ambience sounds."""

    def __init__(self, app, monster: Entity, drip_points: list[Vec3]) -> None:
        bank = SoundBank(app)
        # 3D sound: you hear which side each sound comes from. The volume change
        # with distance is still computed by the game (closeness), hence no drop-off.
        audio3d = Audio3DManager(app.sfxManagerList[0], camera)
        audio3d.setDropOffFactor(0)
        self._monster = MonsterSounds(bank)
        for sound in self._monster.sounds():
            audio3d.attachSoundToObject(sound, monster)
        self._drips = DripSounds(bank, audio3d, drip_points)
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
        self._drips.update(dt)
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


def set_master_volume(app, volume: float) -> None:
    """Master volume of every game sound: 0 = mute, 1 = full volume."""
    app.sfxManagerList[0].setVolume(volume)
