"""Éclairage de la scène : obscurité, brouillard, lampe torche et lumières fixes.

Utilise l'éclairage automatique de Panda3D, le moteur sur lequel Ursina est construit.
"""
import random

from panda3d.core import AmbientLight, Fog, PerspectiveLens, PointLight, Spotlight
from ursina import Entity, camera, color, scene, window

from core.level import Cell
from view.coords import cell_to_world

AMBIENT_COLOR = (0.09, 0.09, 0.11, 1)
FOG_DENSITY = 0.06
FLASHLIGHT_COLOR = (1.0, 0.92, 0.75, 1)
FLASHLIGHT_ANGLE = 65
FLASHLIGHT_ATTENUATION = (1.0, 0.02, 0.008)

EMERGENCY_COLOR = (0.35, 0.03, 0.02, 1)
EMERGENCY_ATTENUATION = (1.0, 0.5, 0.6)
EXIT_COLOR = (0.1, 0.9, 0.3, 1)
EXIT_ATTENUATION = (1.0, 0.3, 0.3)
FIXTURE_SCALE = (0.4, 0.08, 0.4)
FLICKER_CHANCE = 0.02      # probabilité de grésiller, à chaque image
FLICKER_DIM = 0.15         # intensité pendant un grésillement


def make_lit(entity: Entity) -> Entity:
    """Fait réagir une entité aux lumières, à la place du rendu non éclairé d'Ursina."""
    entity.setShaderAuto()
    return entity


class Flicker(Entity):
    """Fait grésiller une lumière : de temps en temps, son intensité chute une image."""

    def __init__(self, light: PointLight, base_color: tuple) -> None:
        super().__init__()
        self._light = light
        self._base_color = base_color

    def update(self) -> None:
        factor = FLICKER_DIM if random.random() < FLICKER_CHANCE else 1.0
        red, green, blue, alpha = self._base_color
        self._light.setColor((red * factor, green * factor, blue * factor, alpha))


class Lighting:
    """Met en place l'ambiance, les lumières fixes, et pilote la lampe torche.

    Cette classe ne décide jamais si la lampe est allumée : c'est le noyau
    (la classe Flashlight) qui le décide, et on le lui indique avec set_flashlight().
    """

    def __init__(self) -> None:
        self._flashlight_node = None
        self._flashlight_on = True

    def setup(self) -> None:
        window.color = color.black
        self._add_ambient_light()
        self._add_fog()
        self._add_flashlight()

    def set_flashlight(self, on: bool) -> None:
        if self._flashlight_node is None:
            raise RuntimeError("Lighting.setup() doit être appelé avant set_flashlight().")
        if on == self._flashlight_on:
            return
        self._flashlight_on = on
        if on:
            scene.setLight(self._flashlight_node)
        else:
            scene.clearLight(self._flashlight_node)

    def add_emergency_lights(self, cells: tuple[Cell, ...], ceiling_height: float) -> None:
        """Lumières de secours rouges qui grésillent."""
        for cell in cells:
            light = self._add_ceiling_light(
                cell, ceiling_height, EMERGENCY_COLOR, EMERGENCY_ATTENUATION, color.red
            )
            Flicker(light, EMERGENCY_COLOR)

    def add_exit_light(self, cell: Cell, ceiling_height: float) -> None:
        """Lumière verte au-dessus de la sortie, repère visible de loin."""
        self._add_ceiling_light(cell, ceiling_height, EXIT_COLOR, EXIT_ATTENUATION, color.lime)

    @staticmethod
    def _add_ceiling_light(
        cell: Cell, ceiling_height: float, light_color: tuple, attenuation: tuple, fixture_color
    ) -> PointLight:
        """Une lumière ponctuelle sous le plafond, avec son boîtier lumineux."""
        light = PointLight("ceiling_light")
        light.setColor(light_color)
        light.setAttenuation(attenuation)
        node = scene.attachNewNode(light)
        node.setPos(cell_to_world(cell, ceiling_height - 0.3))
        scene.setLight(node)
        # Le boîtier n'utilise pas make_lit : il reste toujours pleinement visible.
        Entity(
            model="cube",
            position=cell_to_world(cell, ceiling_height - 0.05),
            scale=FIXTURE_SCALE,
            color=fixture_color,
        )
        return light

    def _add_ambient_light(self) -> None:
        ambient = AmbientLight("ambient")
        ambient.setColor(AMBIENT_COLOR)
        scene.setLight(scene.attachNewNode(ambient))

    def _add_fog(self) -> None:
        fog = Fog("darkness")
        fog.setColor(0, 0, 0)
        fog.setExpDensity(FOG_DENSITY)
        scene.setFog(fog)

    def _add_flashlight(self) -> None:
        flashlight = Spotlight("flashlight")
        flashlight.setColor(FLASHLIGHT_COLOR)
        flashlight.setAttenuation(FLASHLIGHT_ATTENUATION)
        lens = PerspectiveLens()
        lens.setFov(FLASHLIGHT_ANGLE)
        flashlight.setLens(lens)
        self._flashlight_node = camera.attachNewNode(flashlight)
        scene.setLight(self._flashlight_node)