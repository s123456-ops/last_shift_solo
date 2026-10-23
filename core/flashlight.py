"""Lampe torche du joueur : batterie, allumage, recharge.

Module indépendant du moteur de jeu.
"""


class Flashlight:
    """Une lampe dont la batterie se vide quand elle est allumée."""

    def __init__(self, capacity: float, drain_per_second: float) -> None:
        self._capacity = capacity
        self._drain_per_second = drain_per_second
        self._battery = capacity
        self._is_on = False

    @property
    def battery(self) -> float:
        return self._battery

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def charge_ratio(self) -> float:
        return (
            self._battery / self._capacity
        )  # Proportion de batterie restante, entre 0 et 1.

    def toggle(self) -> None:
        if self._is_on:
            self._is_on = False
        elif self._battery > 0:
            self._is_on = True

    def update(self, dt: float) -> None:
        if not self._is_on:
            return
        self._battery = max(self._battery - self._drain_per_second * dt, 0)
        if self._battery == 0:
            self._is_on = False

    def recharge(self, amount: float) -> None:
        self._battery = min(self._battery + amount, self._capacity)
