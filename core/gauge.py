"""Gauge: a value bounded between 0 and a capacity.

Used by composition in Flashlight and Stamina. Engine-independent module.
"""


class Gauge:
    """A value that drains and refills without ever leaving [0, capacity]."""

    def __init__(self, capacity: float) -> None:
        if capacity <= 0:
            raise ValueError("A gauge's capacity must be strictly positive.")
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
