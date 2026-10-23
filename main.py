"""THE LAST SHIFT, version solo : point d'entrée du jeu.

Usage : python main.py
"""

import sys

from ursina import Entity, Text, Ursina, Vec2, application, color, held_keys, time
from ursina.prefabs.first_person_controller import FirstPersonController

from core.flashlight import Flashlight
from core.level import LevelFormatError, load_level
from core.monster import Monster, Situation
from core.stamina import Stamina
from view.coords import cell_to_world, world_to_cell
from view.hud import Hud
from view.level_renderer import WALL_HEIGHT, LevelRenderer
from view.lighting import Lighting
from view.monster_view import MonsterView

LEVEL_PATH = "levels/level1.txt"
MOUSE_SENSITIVITY = Vec2(25, 25)

FLASHLIGHT_CAPACITY = 100
FLASHLIGHT_DRAIN_PER_SECOND = 2  # batterie pleine = 50 secondes d'éclairage

WALK_SPEED = 3
RUN_SPEED = 6
STAMINA_CAPACITY = 100
STAMINA_DRAIN_PER_SECOND = 25  # 4 secondes de course à fond
STAMINA_REGEN_PER_SECOND = 12  # environ 8 secondes pour se recharger

MONSTER_SPEED = 4  # entre la marche (3) et la course (6)
CATCH_DISTANCE = 0.9
MONSTER_PATROL = [(14, 26), (7, 22), (11, 15), (12, 4), (7, 8), (2, 26)]


class GameController(Entity):
    """Relie le noyau à la vue, à chaque image et à chaque touche."""

    def __init__(
        self,
        player: FirstPersonController,
        flashlight: Flashlight,
        stamina: Stamina,
        monster: Monster,
        monster_view: MonsterView,
        lighting: Lighting,
        hud: Hud,
    ) -> None:
        super().__init__()
        self._player = player
        self._flashlight = flashlight
        self._stamina = stamina
        self._monster = monster
        self._monster_view = monster_view
        self._lighting = lighting
        self._hud = hud
        self._game_over = False

    def input(self, key: str) -> None:
        if key == "f":
            self._flashlight.toggle()
        elif key == "escape":
            application.quit()

    def update(self) -> None:
        if self._game_over:
            return
        self._update_flashlight()
        self._update_stamina()
        self._update_monster()

    def _update_flashlight(self) -> None:
        self._flashlight.update(time.dt)
        self._lighting.set_flashlight(self._flashlight.is_on)
        self._hud.show_battery(self._flashlight.charge_ratio)

    def _update_stamina(self) -> None:
        is_moving = self._player.direction.length() > 0
        wants_to_run = is_moving and held_keys["shift"]
        self._stamina.update(time.dt, wants_to_run)
        self._player.speed = RUN_SPEED if self._stamina.is_running else WALK_SPEED
        self._hud.show_stamina(self._stamina.charge_ratio, self._stamina.is_exhausted)

    def _update_monster(self) -> None:
        if self._monster_view.has_arrived():
            situation = Situation(
                player_cell=world_to_cell(self._player.position),
                player_running=self._stamina.is_running,
                flashlight_on=self._flashlight.is_on,
            )
            self._monster_view.move_to(self._monster.step(situation))
        self._monster_view.advance(time.dt)
        if self._monster_caught_player():
            self._end_game("Le poste de gardien de nuit est à nouveau vacant.")

    def _monster_caught_player(self) -> bool:
        gap = self._monster_view.position - self._player.position
        return Vec2(gap.x, gap.z).length() < CATCH_DISTANCE

    def _end_game(self, message: str) -> None:
        self._game_over = True
        self._player.enabled = False
        Text(message, origin=(0, 0), scale=2, color=color.red)


def main() -> None:
    try:
        level = load_level(LEVEL_PATH)
        monster = Monster(level, level.monster_start, MONSTER_PATROL)
    except (FileNotFoundError, LevelFormatError, ValueError) as error:
        sys.exit(f"Impossible de préparer la partie : {error}")

    app = Ursina()
    LevelRenderer(level).build()

    player = FirstPersonController(position=cell_to_world(level.player_start))
    player.mouse_sensitivity = MOUSE_SENSITIVITY
    lighting = Lighting()
    lighting.setup()
    lighting.add_emergency_lights(level.emergency_light_cells, WALL_HEIGHT)
    lighting.add_exit_light(level.exit_cell, WALL_HEIGHT)

    flashlight = Flashlight(FLASHLIGHT_CAPACITY, FLASHLIGHT_DRAIN_PER_SECOND)
    stamina = Stamina(
        STAMINA_CAPACITY, STAMINA_DRAIN_PER_SECOND, STAMINA_REGEN_PER_SECOND
    )
    monster_view = MonsterView(app, level.monster_start, MONSTER_SPEED)
    GameController(player, flashlight, stamina, monster, monster_view, lighting, Hud())
    app.run()


if __name__ == "__main__":
    main()
