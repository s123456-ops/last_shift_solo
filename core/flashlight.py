"""The player's flashlight: battery, switching on and off, recharging.

Engine-independent module.
"""

from core.gauge import Gauge


class Flashlight:
    """A flashlight whose battery drains while it is on."""

    def __init__(self, capacity: float, drain_per_second: float) -> None:
        self._battery = Gauge(capacity)
        self._drain_per_second = drain_per_second
        self._is_on = False

    @property
    def battery(self) -> float:
        return self._battery.value

    @property
    def charge_ratio(self) -> float:
        return self._battery.ratio

    @property
    def is_on(self) -> bool:
        return self._is_on

    def toggle(self) -> None:
        if self._is_on:
            self._is_on = False
        elif not self._battery.is_empty:
            self._is_on = True

    def update(self, dt: float) -> None:
        if not self._is_on:
            return
        self._battery.drain(self._drain_per_second * dt)
        if self._battery.is_empty:
            self._is_on = False

    def recharge(self, amount: float) -> None:
        self._battery.fill(amount)
