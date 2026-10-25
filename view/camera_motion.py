"""Mouvements de caméra qui donnent du poids au joueur : balancement et retard.

N'importe pas Ursina : les calculs se testent sans fenêtre.
"""

import math

WALK_AMPLITUDE = 0.035  # mètres : la tête monte et descend en marchant
RUN_AMPLITUDE = 0.08
WALK_FREQUENCY = 1.7  # foulées par seconde
RUN_FREQUENCY = 2.6
SETTLE_SPEED = 6.0  # vitesse à laquelle le balancement apparaît ou s'éteint
SIDEWAYS_RATIO = 0.5  # le balancement latéral est deux fois plus faible


def approach_angle(current: float, target: float, ratio: float) -> float:
    """Rapproche un angle d'un autre par le chemin le plus court (359° → 1° : +2°)."""
    difference = (target - current + 180) % 360 - 180
    return current + difference * max(0.0, min(1.0, ratio))


class HeadBob:
    """Le balancement de la tête : deux oscillations verticales par foulée, une latérale."""

    def __init__(self) -> None:
        self._phase = 0.0
        self._amount = 0.0

    def update(self, dt: float, moving: bool, running: bool) -> tuple[float, float]:
        """Renvoie le décalage (vertical, latéral) de la caméra, en mètres."""
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
