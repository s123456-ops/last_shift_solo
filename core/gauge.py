"""Jauge : une valeur bornée entre 0 et une capacité.

Utilisée par composition dans Flashlight et Stamina. Module indépendant du moteur.
"""


class Gauge:
    """Une valeur qui se vide et se remplit sans jamais sortir de [0, capacité]."""

    def __init__(self, capacity: float) -> None:
        if capacity <= 0:
            raise ValueError("La capacité d'une jauge doit être strictement positive.")
        self._capacity = capacity
        self._value = capacity

    @property
    def value(self) -> float:
        return self._value

    @property
    def ratio(self) -> float:
        return self._value / self._capacity

    @property
    def is_empty(self) -> bool:
        return self._value == 0

    def drain(self, amount: float) -> None:
        self._value = max(self._value - amount, 0)

    def fill(self, amount: float) -> None:
        self._value = min(self._value + amount, self._capacity)
