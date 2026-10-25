"""Monster display: the 3D model glides from one cell to the next."""

import math

from ursina import Entity, Vec3, color

from core.level import Cell
from view.coords import cell_to_world
from view.lighting import make_lit
from view.model_loader import MONSTER, ModelLoadError, place_model

ARRIVAL_TOLERANCE = 0.01
STEP_FREQUENCY = 5  # steps per second (in radians, about 0.8 steps/s)
BOB_HEIGHT = 0.08  # amplitude of the vertical bob, in metres
SWAY_ANGLE = 4  # sideways tilt, in degrees


class MonsterView:
    """Smoothly moves the model towards the cell decided by the core."""

    def __init__(self, app, start: Cell, speed: float) -> None:
        self._entity = Entity(position=cell_to_world(start))
        self._body = Entity(parent=self._entity)
        self._target = self._entity.position
        self._speed = speed
        self._walk_time = 0.0
        try:
            place_model(app, MONSTER, self._body)
        except ModelLoadError as error:
            print(f"Warning: {error}. The monster is replaced by a red block.")
            make_lit(
                Entity(
                    parent=self._body,
                    model="cube",
                    color=color.red,
                    scale=(0.8, 2.4, 0.8),
                    y=1.2,
                )
            )

    @property
    def entity(self) -> Entity:
        """The moving point: the monster's sounds are attached to it."""
        return self._entity

    @property
    def position(self) -> Vec3:
        return self._entity.position

    def has_arrived(self) -> bool:
        return (self._target - self._entity.position).length() < ARRIVAL_TOLERANCE

    def move_to(self, cell: Cell) -> None:
        self._target = cell_to_world(cell)
        direction = self._target - self._entity.position
        if direction.length() > 0:
            self._entity.rotation_y = (
                math.degrees(math.atan2(direction.x, direction.z)) + 180
            )

    def set_speed(self, speed: float) -> None:
        self._speed = speed

    def advance(self, dt: float) -> None:
        to_target = self._target - self._entity.position
        step = self._speed * dt
        if to_target.length() <= step:
            self._entity.position = self._target
        else:
            self._entity.position += to_target.normalized() * step
        self._animate_walk(dt)

    def _animate_walk(self, dt: float) -> None:
        """Bob and limp, without a skeleton: the whole body is shaken."""
        self._walk_time += dt
        phase = self._walk_time * STEP_FREQUENCY
        self._body.y = abs(math.sin(phase)) * BOB_HEIGHT
        self._body.rotation_z = math.sin(phase / 2) * SWAY_ANGLE
