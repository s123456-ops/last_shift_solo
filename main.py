"""THE LAST SHIFT, version solo : point d'entrée du jeu.

Usage : python main.py
"""

import sys

from ursina import Entity, Text, Ursina, Vec2, application, color, held_keys, time
from ursina.prefabs.first_person_controller import FirstPersonController

from core.flashlight import Flashlight
from core.interactables import BatteryPickup, HidingSpot, Interactions
from core.level import LevelFormatError, load_level
from core.monster import Monster, Situation
from core.player import Player
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
BATTERY_CHARGE = 40  # une pile recharge 40 % de la batterie

WALK_SPEED = 3
RUN_SPEED = 6
STAMINA_CAPACITY = 100
STAMINA_DRAIN_PER_SECOND = 25  # 4 secondes de course à fond
STAMINA_REGEN_PER_SECOND = 12  # environ 8 secondes pour se recharger

MONSTER_PATROL_SPEED = 2  # il rôde, plus lent que votre marche
MONSTER_CHASE_SPEED = 4  # il fonce : seule la course permet de le distancer
MONSTER_GRACE_PERIOD = 20  # secondes avant qu'il ne commence à bouger
PEACEFUL_MODE = False  # True pour tester sans le monstre
CATCH_DISTANCE = 0.9
MONSTER_PATROL = [(14, 26), (7, 22), (11, 15), (12, 4), (7, 8), (2, 26)]


class GameController(Entity):
    """Relie le noyau à la vue, à chaque image et à chaque touche."""

    def __init__(
        self,
        first_person: FirstPersonController,
        player: Player,
        monster: Monster,
        monster_view: MonsterView,
        interactions: Interactions,
        renderer: LevelRenderer,
        lighting: Lighting,
        hud: Hud,
    ) -> None:
        super().__init__()
        self._first_person = first_person
        self._player = player
        self._monster = monster
        self._monster_view = monster_view
        self._interactions = interactions
        self._renderer = renderer
        self._lighting = lighting
        self._hud = hud
        self._game_over = False
        self._elapsed = 0.0
        self._position_before_hiding = first_person.position

    def input(self, key: str) -> None:
        if key == "escape":
            application.quit()
        if self._game_over:
            return
        if key == "f" and not self._player.is_hidden:
            self._player.flashlight.toggle()
        elif key == "e":
            self._interact()

    def update(self) -> None:
        if self._game_over:
            return
        self._update_flashlight()
        self._update_stamina()
        self._update_interaction()
        self._update_monster()

    def _player_cell(self):
        return world_to_cell(self._first_person.position)

    def _update_flashlight(self) -> None:
        flashlight = self._player.flashlight
        flashlight.update(time.dt)
        self._lighting.set_flashlight(flashlight.is_on)
        self._hud.show_battery(flashlight.charge_ratio)

    def _update_stamina(self) -> None:
        stamina = self._player.stamina
        is_moving = (
            self._first_person.enabled and self._first_person.direction.length() > 0
        )
        stamina.update(time.dt, is_moving and held_keys["shift"])
        self._first_person.speed = RUN_SPEED if stamina.is_running else WALK_SPEED
        self._hud.show_stamina(stamina.charge_ratio, stamina.is_exhausted)

    def _update_interaction(self) -> None:
        item = self._interactions.near(self._player_cell())
        self._hud.show_prompt(item.prompt if item else None)

    def _interact(self) -> None:
        item = self._interactions.near(self._player_cell())
        if item is None:
            return
        was_hidden = self._player.is_hidden
        self._hud.show_message(item.interact(self._player))
        if item.is_consumed:
            self._renderer.remove_item(item.cell)
        if self._player.is_hidden != was_hidden:
            self._apply_hiding(item.cell)

    def _apply_hiding(self, cell) -> None:
        """Place la caméra dans le casier, ou la ressort là où le joueur est entré."""
        hidden = self._player.is_hidden
        if hidden:
            self._position_before_hiding = self._first_person.position
            self._first_person.position = cell_to_world(cell)
        else:
            self._first_person.position = self._position_before_hiding
        self._first_person.enabled = not hidden
        self._hud.show_hiding(hidden)

    def _update_monster(self) -> None:
        self._elapsed += time.dt
        if PEACEFUL_MODE or self._elapsed < MONSTER_GRACE_PERIOD:
            return
        if self._monster_view.has_arrived():
            situation = Situation(
                player_cell=self._player_cell(),
                player_running=self._player.stamina.is_running,
                flashlight_on=self._player.flashlight.is_on,
                player_hidden=self._player.is_hidden,
            )
            self._monster_view.move_to(self._monster.step(situation))
            speed = (
                MONSTER_CHASE_SPEED
                if self._monster.is_chasing
                else MONSTER_PATROL_SPEED
            )
            self._monster_view.set_speed(speed)
        self._monster_view.advance(time.dt)
        if self._monster_caught_player():
            self._end_game("Le poste de gardien de nuit est à nouveau vacant.")

    def _monster_caught_player(self) -> bool:
        gap = self._monster_view.position - self._first_person.position
        return Vec2(gap.x, gap.z).length() < CATCH_DISTANCE

    def _end_game(self, message: str) -> None:
        self._game_over = True
        self._first_person.enabled = False
        self._hud.show_prompt(None)
        self._hud.show_hiding(False)
        Text(message, origin=(0, 0), scale=2, color=color.red)


def main() -> None:
    try:
        level = load_level(LEVEL_PATH)
        monster = Monster(level, level.monster_start, MONSTER_PATROL)
        interactions = Interactions(
            [BatteryPickup(cell, BATTERY_CHARGE) for cell in level.battery_cells]
            + [HidingSpot(cell) for cell in level.hiding_spot_cells]
        )
    except (FileNotFoundError, LevelFormatError, ValueError) as error:
        sys.exit(f"Impossible de préparer la partie : {error}")

    app = Ursina()
    renderer = LevelRenderer(level)
    renderer.build()

    first_person = FirstPersonController(position=cell_to_world(level.player_start))
    first_person.mouse_sensitivity = MOUSE_SENSITIVITY
    lighting = Lighting()
    lighting.setup()
    lighting.add_emergency_lights(level.emergency_light_cells, WALL_HEIGHT)
    lighting.add_exit_light(level.exit_cell, WALL_HEIGHT)

    player = Player(
        Flashlight(FLASHLIGHT_CAPACITY, FLASHLIGHT_DRAIN_PER_SECOND),
        Stamina(STAMINA_CAPACITY, STAMINA_DRAIN_PER_SECOND, STAMINA_REGEN_PER_SECOND),
    )
    monster_view = MonsterView(app, level.monster_start, MONSTER_PATROL_SPEED)
    GameController(
        first_person,
        player,
        monster,
        monster_view,
        interactions,
        renderer,
        lighting,
        Hud(),
    )
    app.run()


if __name__ == "__main__":
    main()
