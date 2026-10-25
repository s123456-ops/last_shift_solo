"""State of the building: power and exit. Engine-independent module."""


class Facility:
    """Shared by the generator and the exit door."""

    def __init__(self) -> None:
        self._power_on = False
        self._exit_reached = False

    @property
    def power_on(self) -> bool:
        return self._power_on

    @property
    def exit_reached(self) -> bool:
        return self._exit_reached

    def restore_power(self) -> None:
        self._power_on = True

    def reach_exit(self) -> None:
        if not self._power_on:
            raise RuntimeError("The exit stays locked until the power is restored.")
        self._exit_reached = True
