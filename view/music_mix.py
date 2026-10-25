"""The music volume for each moment of the game, and its fades.

Does not import Ursina: tested without a window.
"""

MOODS = {  # moment -> music volume (0 to 1)
    "title": 0.55,  # the title screen sets up the dread
    "intro": 0.4,  # the story is told over it
    "game": 0.1,  # barely audible: the building's noises come first
    "chase": 0.03,  # almost silent: you must hear the monster coming
    "silent": 0.0,  # fin de partie
}
FADE_PER_SECOND = 0.25  # fade speed: from 0.55 to 0.1 in under 2 seconds


def next_volume(current: float, target: float, dt: float) -> float:
    """Moves one step towards the wanted volume, never past it."""
    step = FADE_PER_SECOND * dt
    if abs(target - current) <= step:
        return target
    return current + step if target > current else current - step
