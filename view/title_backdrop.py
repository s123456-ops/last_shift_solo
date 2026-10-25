"""Title screen backdrop: a slow walk down the corridor, a silhouette at the end."""

import math

from ursina import Entity, camera, destroy, lerp, time

from core.level import Cell
from view.coords import cell_to_world
from view.model_loader import MONSTER, ModelLoadError, place_model

EYE_HEIGHT = 1.6  # camera height, in metres
TRAVEL_DURATION = 45.0  # seconds to walk the corridor, before starting over
SWAY_ANGLE = 1.5  # head sway, in degrees
TILT_ANGLE = 0.8


class TitleBackdrop(Entity):
    """Moves the camera through the game scenery during the title screen."""

    def __init__(self, app, start: Cell, end: Cell, silhouette: Cell) -> None:
        super().__init__()
        self._start = cell_to_world(start, EYE_HEIGHT)
        self._end = cell_to_world(end, EYE_HEIGHT)
        direction = self._end - self._start
        self._heading = math.degrees(math.atan2(direction.x, direction.z))
        self._elapsed = 0.0
        self._silhouette = self._place_silhouette(app, silhouette)
        camera.position = self._start
        camera.rotation = (0, self._heading, 0)

    def update(self) -> None:
        self._elapsed += time.dt
        progress = (self._elapsed / TRAVEL_DURATION) % 1.0
        camera.position = lerp(self._start, self._end, progress)
        camera.rotation_y = self._heading + math.sin(self._elapsed * 0.5) * SWAY_ANGLE
        camera.rotation_x = math.sin(self._elapsed * 0.3) * TILT_ANGLE

    def stop(self) -> None:
        destroy(self._silhouette)
        destroy(self)

    def _place_silhouette(self, app, cell: Cell) -> Entity:
        """The monster, standing still at the end of the corridor, facing the camera."""
        holder = Entity(position=cell_to_world(cell))
        facing = self._start - holder.position
        holder.rotation_y = math.degrees(math.atan2(facing.x, facing.z)) + 180
        try:
            place_model(app, MONSTER, holder)
        except ModelLoadError:
            pass  # without a model, the corridor stays empty: the title screen still works
        return holder
