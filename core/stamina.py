"""Endurance du joueur : se vide en courant, se recharge en marchant.

Module indépendant du moteur de jeu.
"""

from core.gauge import Gauge


class Stamina:
    """Décide si le joueur peut courir, et gère l'épuisement."""

    def __init__(
        self,
        capacity: float,
        drain_per_second: float,
        regen_per_second: float,
        recovery_ratio: float = 0.3,
    ) -> None:
        self._gauge = Gauge(capacity)
        self._drain_per_second = drain_per_second
        self._regen_per_second = regen_per_second
        self._recovery_ratio = recovery_ratio
        self._is_exhausted = False
        self._is_running = False

    @property
    def value(self) -> float:
        return self._gauge.value

    @property
    def charge_ratio(self) -> float:
        return self._gauge.ratio

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_exhausted(self) -> bool:
        return self._is_exhausted

    def update(self, dt: float, wants_to_run: bool) -> None:
        """wants_to_run : le joueur se déplace en tenant la touche de course."""
        self._is_running = wants_to_run and not self._is_exhausted
        if self._is_running:
            self._run(dt)
        else:
            self._recover(dt)

    def _run(self, dt: float) -> None:
        self._gauge.drain(self._drain_per_second * dt)
        if self._gauge.is_empty:
            self._is_exhausted = True
            self._is_running = False

    def _recover(self, dt: float) -> None:
        self._gauge.fill(self._regen_per_second * dt)
        if self._is_exhausted and self._gauge.ratio >= self._recovery_ratio:
            self._is_exhausted = False
