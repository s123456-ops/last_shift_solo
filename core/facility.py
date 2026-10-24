"""État du bâtiment : le courant et la sortie. Module indépendant du moteur de jeu."""


class Facility:
    """Partagé par le tableau électrique et la porte de sortie."""

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
            raise RuntimeError(
                "La sortie est verrouillée tant que le courant n'est pas rétabli."
            )
        self._exit_reached = True
