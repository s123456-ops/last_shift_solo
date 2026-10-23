"""Affichage du monstre : le modèle 3D glisse d'une case à l'autre."""

import math

from ursina import Entity, Vec3, color

from core.level import Cell
from view.coords import cell_to_world
from view.lighting import make_lit
from view.model_loader import MONSTER, ModelLoadError, place_model

ARRIVAL_TOLERANCE = 0.01
STEP_FREQUENCY = 5  # pas par seconde (en radians, environ 0,8 pas/s)
BOB_HEIGHT = 0.08  # amplitude du balancement vertical, en mètres
SWAY_ANGLE = 4  # inclinaison de côté, en degrés


class MonsterView:
    """Déplace le modèle en douceur vers la case décidée par le noyau."""

    def __init__(self, app, start: Cell, speed: float) -> None:
        self._entity = Entity(position=cell_to_world(start))
        self._body = Entity(parent=self._entity)
        self._target = self._entity.position
        self._speed = speed
        self._walk_time = 0.0
        try:
            place_model(app, MONSTER, self._body)
        except ModelLoadError as error:
            print(
                f"Avertissement : {error}. Le monstre est remplacé par un bloc rouge."
            )
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

    def advance(self, dt: float) -> None:
        to_target = self._target - self._entity.position
        step = self._speed * dt
        if to_target.length() <= step:
            self._entity.position = self._target
        else:
            self._entity.position += to_target.normalized() * step
        self._animate_walk(dt)

    def _animate_walk(self, dt: float) -> None:
        """Balancement et boitement, sans squelette : on agite tout le corps."""
        self._walk_time += dt
        phase = self._walk_time * STEP_FREQUENCY
        self._body.y = abs(math.sin(phase)) * BOB_HEIGHT
        self._body.rotation_z = math.sin(phase / 2) * SWAY_ANGLE
