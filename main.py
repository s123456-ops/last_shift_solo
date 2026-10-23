"""THE LAST SHIFT, version solo : point d'entrée du jeu.

Usage : python main.py
"""

import sys

from ursina import Entity, Ursina, Vec2, application, time
from ursina.prefabs.first_person_controller import FirstPersonController

from core.flashlight import Flashlight
from core.level import LevelFormatError, load_level
from view.coords import cell_to_world
from view.hud import Hud
from view.level_renderer import WALL_HEIGHT, LevelRenderer
from view.lighting import Lighting
from view.model_loader import MONSTER, ModelLoadError, place_model

LEVEL_PATH = "levels/level1.txt"
MOUSE_SENSITIVITY = Vec2(25, 25)
FLASHLIGHT_CAPACITY = 100
FLASHLIGHT_DRAIN_PER_SECOND = 2  # batterie pleine = 50 secondes d'éclairage


class GameController(Entity):
    """Relie le noyau à la vue, à chaque image et à chaque touche."""

    def __init__(self, flashlight: Flashlight, lighting: Lighting, hud: Hud) -> None:
        super().__init__()
        self._flashlight = flashlight
        self._lighting = lighting
        self._hud = hud

    def input(self, key: str) -> None:
        if key == "f":
            self._flashlight.toggle()
        elif key == "escape":
            application.quit()

    def update(self) -> None:
        self._flashlight.update(time.dt)
        self._lighting.set_flashlight(self._flashlight.is_on)
        self._hud.show_battery(self._flashlight.charge_ratio)


def main() -> None:
    try:
        level = load_level(LEVEL_PATH)
    except (FileNotFoundError, LevelFormatError) as error:
        sys.exit(f"Impossible de charger le niveau : {error}")

    app = Ursina()
    LevelRenderer(level).build()
    monster = Entity(position=cell_to_world(level.monster_start))
    try:
        place_model(app, MONSTER, monster)
    except ModelLoadError as error:
        print(f"Avertissement : {error}. Le niveau s'affiche sans le monstre.")

    player = FirstPersonController(position=cell_to_world(level.player_start))
    player.mouse_sensitivity = MOUSE_SENSITIVITY
    lighting = Lighting()
    lighting.setup()
    lighting.add_emergency_lights(level.emergency_light_cells, WALL_HEIGHT)
    lighting.add_exit_light(level.exit_cell, WALL_HEIGHT)

    flashlight = Flashlight(FLASHLIGHT_CAPACITY, FLASHLIGHT_DRAIN_PER_SECOND)
    GameController(flashlight, lighting, Hud())
    app.run()


if __name__ == "__main__":
    main()
