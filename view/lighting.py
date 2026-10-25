"""Scene lighting: darkness, fog, flashlight and fixed lights.

Uses the automatic lighting of Panda3D, the engine Ursina is built on.
"""

import random

from panda3d.core import AmbientLight, Fog, PerspectiveLens, PointLight, Spotlight
from ursina import Entity, camera, color, scene, time, window

from core.level import Cell
from view.camera_motion import approach_angle
from view.coords import cell_to_world

AMBIENT_COLOR = (0.025, 0.025, 0.03, 1)  # avant : 0.09
FOG_DENSITY = 0.09  # avant : 0.06
FLASHLIGHT_COLOR = (1.0, 0.92, 0.75, 1)
FLASHLIGHT_ANGLE = 65
FLASHLIGHT_ATTENUATION = (1.0, 0.02, 0.008)

EMERGENCY_COLOR = (0.25, 0.02, 0.01, 1)  # avant : 0.35
EMERGENCY_ATTENUATION = (1.0, 0.5, 0.6)
EXIT_COLOR = (0.1, 0.9, 0.3, 1)
EXIT_ATTENUATION = (1.0, 0.3, 0.3)
FIXTURE_SCALE = (0.4, 0.08, 0.4)
FLICKER_CHANCE = 0.02  # chance of flickering, every frame
FLICKER_DIM = 0.15  # intensity during a flicker
FLASHLIGHT_FOLLOW_SPEED = (
    12  # the lower it is, the more the flashlight lags behind your gaze
)
FLASHLIGHT_TREMBLE = 1.2  # degrees: the hand shakes when out of breath


def make_lit(entity: Entity) -> Entity:
    """Makes an entity react to lights, instead of Ursina's unlit rendering."""
    entity.setShaderAuto()
    return entity


class Flicker(Entity):
    """Makes a light flicker: every now and then, its intensity drops for one frame."""

    def __init__(self, light: PointLight, base_color: tuple) -> None:
        super().__init__()
        self._light = light
        self._base_color = base_color

    def update(self) -> None:
        factor = FLICKER_DIM if random.random() < FLICKER_CHANCE else 1.0
        red, green, blue, alpha = self._base_color
        self._light.setColor((red * factor, green * factor, blue * factor, alpha))


class FlashlightRig(Entity):
    """The hand holding the flashlight: it follows your gaze, with a slight lag.

    Ursina calls update() every frame, even on the title screen.
    """

    def __init__(self) -> None:
        super().__init__()
        self.trembling = False

    def update(self) -> None:
        self.world_position = camera.world_position
        ratio = time.dt * FLASHLIGHT_FOLLOW_SPEED
        self.rotation_x = approach_angle(
            self.rotation_x, camera.world_rotation_x, ratio
        )
        self.rotation_y = approach_angle(
            self.rotation_y, camera.world_rotation_y, ratio
        )
        if self.trembling:
            self.rotation_x += random.uniform(-1, 1) * FLASHLIGHT_TREMBLE
            self.rotation_y += random.uniform(-1, 1) * FLASHLIGHT_TREMBLE


class Lighting:
    """Sets up the ambience and fixed lights, and drives the flashlight.

    This class never decides whether the flashlight is on: the core does
    (the Flashlight class), and tells it through set_flashlight().
    """

    def __init__(self) -> None:
        self._flashlight_node = None
        self._flashlight_on = True
        self._ambient = None
        self._fog = None
        self._rig: FlashlightRig | None = None

    def setup(self) -> None:
        window.color = color.black
        self._add_ambient_light()
        self._add_fog()
        self._add_flashlight()

    def set_flashlight(self, on: bool) -> None:
        if self._flashlight_node is None:
            raise RuntimeError(
                "Lighting.setup() must be called before set_flashlight()."
            )
        if on == self._flashlight_on:
            return
        self._flashlight_on = on
        if on:
            scene.setLight(self._flashlight_node)
        else:
            scene.clearLight(self._flashlight_node)

    def set_trembling(self, trembling: bool) -> None:
        """The flashlight shakes while the player is out of breath."""
        if self._rig is not None:
            self._rig.trembling = trembling

    def set_brightness(self, factor: float) -> None:
        """Brightens (factor > 1) or darkens (factor < 1) the ambience and the fog.

        The flashlight and emergency lights do not change: only the overall
        gloom adapts to the player's screen.
        """
        if self._ambient is None or self._fog is None:
            raise RuntimeError(
                "Lighting.setup() must be called before set_brightness()."
            )
        red, green, blue, alpha = AMBIENT_COLOR
        self._ambient.setColor((red * factor, green * factor, blue * factor, alpha))
        self._fog.setExpDensity(FOG_DENSITY / factor)

    def add_emergency_lights(
        self, cells: tuple[Cell, ...], ceiling_height: float
    ) -> None:
        """Red emergency lights that flicker."""
        for cell in cells:
            light = self._add_ceiling_light(
                cell, ceiling_height, EMERGENCY_COLOR, EMERGENCY_ATTENUATION, color.red
            )
            Flicker(light, EMERGENCY_COLOR)

    def add_exit_light(self, cell: Cell, ceiling_height: float) -> None:
        """Green light above the exit, a landmark visible from afar."""
        self._add_ceiling_light(
            cell, ceiling_height, EXIT_COLOR, EXIT_ATTENUATION, color.lime
        )

    @staticmethod
    def _add_ceiling_light(
        cell: Cell,
        ceiling_height: float,
        light_color: tuple,
        attenuation: tuple,
        fixture_color,
    ) -> PointLight:
        """A point light under the ceiling, with its glowing fixture."""
        light = PointLight("ceiling_light")
        light.setColor(light_color)
        light.setAttenuation(attenuation)
        node = scene.attachNewNode(light)
        node.setPos(cell_to_world(cell, ceiling_height - 0.3))
        scene.setLight(node)
        # The fixture does not use make_lit: it always stays fully visible.
        Entity(
            model="cube",
            position=cell_to_world(cell, ceiling_height - 0.05),
            scale=FIXTURE_SCALE,
            color=fixture_color,
        )
        return light

    def _add_ambient_light(self) -> None:
        self._ambient = AmbientLight("ambient")
        self._ambient.setColor(AMBIENT_COLOR)
        scene.setLight(scene.attachNewNode(self._ambient))

    def _add_fog(self) -> None:
        self._fog = Fog("darkness")
        self._fog.setColor(0, 0, 0)
        self._fog.setExpDensity(FOG_DENSITY)
        scene.setFog(self._fog)

    def _add_flashlight(self) -> None:
        flashlight = Spotlight("flashlight")
        flashlight.setColor(FLASHLIGHT_COLOR)
        flashlight.setAttenuation(FLASHLIGHT_ATTENUATION)
        lens = PerspectiveLens()
        lens.setFov(FLASHLIGHT_ANGLE)
        flashlight.setLens(lens)
        self._rig = FlashlightRig()
        self._flashlight_node = self._rig.attachNewNode(flashlight)
        scene.setLight(self._flashlight_node)
