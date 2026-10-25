"""Player sounds: footsteps, breathing, heartbeat, flashlight, pickup, locker."""

from view.sound_bank import LoopChannel, SoundBank

WALK_STEP_INTERVAL = 0.55  # seconds between two footsteps while walking
RUN_STEP_INTERVAL = 0.32  # seconds between two footsteps while running
WALK_VOLUME = 0.25  # always quieter than the monster's footsteps
RUN_VOLUME = 0.4
BREATH_VOLUME = 0.5
HEART_MAX_VOLUME = 0.8
HEART_THRESHOLD = 0.15  # below this closeness, the heart stays calm and silent
HEART_MAX_SPEEDUP = 0.6  # the heart beats up to 60 % faster
CLICK_VOLUME = 0.5
PICKUP_VOLUME = 0.4
LOCKER_VOLUME = 0.6


class PlayerSounds:
    """The sounds the player makes, or feels."""

    def __init__(self, bank: SoundBank) -> None:
        self._bank = bank
        self._walk = bank.load("player", "player_step_*.ogg")
        self._run = bank.load("player", "player_run_*.ogg")
        self._light_on = bank.load("player", "flashlight_on.ogg")
        self._light_off = bank.load("player", "flashlight_off.ogg")
        self._pickup = bank.load("player", "pickup.ogg")
        self._locker = bank.load("player", "locker.ogg")
        self._breath = LoopChannel(bank.load_one("player", "player_breath.ogg"))
        self._heart = LoopChannel(bank.load_one("player", "player_heartbeat.ogg"))
        self._step_timer = 0.0

    def update(
        self,
        dt: float,
        moving: bool,
        running: bool,
        exhausted: bool,
        closeness: float,
        chased: bool,
    ) -> None:
        self._update_steps(dt, moving, running)
        self._breath.set(BREATH_VOLUME if exhausted else 0.0)
        self._breath.update(dt)
        tension = (
            1.0
            if chased
            else max(0.0, (closeness - HEART_THRESHOLD) / (1 - HEART_THRESHOLD))
        )
        self._heart.set(
            HEART_MAX_VOLUME * tension, rate=1.0 + HEART_MAX_SPEEDUP * tension
        )
        self._heart.update(dt)

    def on_flashlight(self, on: bool) -> None:
        self._bank.play(self._light_on if on else self._light_off, CLICK_VOLUME)

    def on_pickup(self) -> None:
        self._bank.play(self._pickup, PICKUP_VOLUME)

    def on_locker(self) -> None:
        self._bank.play(self._locker, LOCKER_VOLUME)

    def stop_all(self) -> None:
        self._breath.stop()
        self._heart.stop()

    def _update_steps(self, dt: float, moving: bool, running: bool) -> None:
        if not moving:
            self._step_timer = (
                0.0  # the first step sounds as soon as the player moves again
            )
            return
        self._step_timer -= dt
        if self._step_timer > 0:
            return
        self._bank.play(
            self._run if running else self._walk, RUN_VOLUME if running else WALK_VOLUME
        )
        self._step_timer = RUN_STEP_INTERVAL if running else WALK_STEP_INTERVAL
