"""Outil : se promener dans un niveau pour tester la carte et l'éclairage.

Usage, depuis la racine du projet :
    python -m tools.preview_level                    (niveau par défaut)
    python -m tools.preview_level levels/autre.txt   (un autre niveau)
"""

import sys

from ursina import Entity, Ursina, Vec2, application
from ursina.prefabs.first_person_controller import FirstPersonController

from core.level import LevelFormatError, load_level
from view.coords import cell_to_world
from view.level_renderer import WALL_HEIGHT, LevelRenderer
from view.lighting import Lighting
from view.model_loader import MONSTER, ModelLoadError, place_model


DEFAULT_LEVEL = "levels/level1.txt"
MOUSE_SENSITIVITY = Vec2(25, 25)


class PreviewControls(Entity):
    """F : allumer/éteindre la lampe. Échap : quitter."""

    def __init__(self, lighting: Lighting) -> None:
        super().__init__()
        self._lighting = lighting
        self._flashlight_on = True

    def input(self, key: str) -> None:
        if key == "f":
            self._flashlight_on = not self._flashlight_on
            self._lighting.set_flashlight(self._flashlight_on)
        elif key == "escape":
            application.quit()


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LEVEL
    try:
        level = load_level(path)
    except FileNotFoundError:
        sys.exit(f"Niveau introuvable : {path}")
    except LevelFormatError as error:
        sys.exit(f"Niveau invalide ({path}) : {error}")

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
    PreviewControls(lighting)
    app.run()


if __name__ == "__main__":
    main()
