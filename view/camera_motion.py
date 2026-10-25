"""Camera movements that give the player weight: head bob and lag.

Does not import Ursina: the maths is tested without a window.
"""

import math

WALK_AMPLITUDE = 0.035  # metres: the head goes up and down while walking
RUN_AMPLITUDE = 0.08
WALK_FREQUENCY = 1.7  # strides per second
RUN_FREQUENCY = 2.6
SETTLE_SPEED = 6.0  # how fast the bob appears or fades
SIDEWAYS_RATIO = 0.5  # the sideways bob is half as strong


def approach_angle(current: float, target: float, ratio: float) -> float:
    """Moves an angle towards another by the shortest way (359° -> 1°: +2°)."""
    difference = (target - current + 180) % 360 - 180
    return current + difference * max(0.0, min(1.0, ratio))


class HeadBob:
    """Head bob: two vertical oscillations per stride, one sideways."""

    def __init__(self) -> None:
        self._phase = 0.0
        self._amount = 0.0

    def update(self, dt: float, moving: bool, running: bool) -> tuple[float, float]:
        """Returns the camera offset (vertical, sideways), in metres."""
        if running:
            target, frequency = RUN_AMPLITUDE, RUN_FREQUENCY
        elif moving:
            target, frequency = WALK_AMPLITUDE, WALK_FREQUENCY
        else:
            target, frequency = 0.0, WALK_FREQUENCY
        self._amount += (target - self._amount) * min(1.0, dt * SETTLE_SPEED)
        if moving:
            self._phase += dt * frequency * 2 * math.pi
        vertical = math.sin(2 * self._phase) * self._amount
        sideways = math.sin(self._phase) * self._amount * SIDEWAYS_RATIO
        return vertical, sideways
