"""THE LAST SHIFT, version solo : point d'entrée du jeu.

Usage : python main.py
"""
import sys

from ursina import Entity, Ursina, Vec2, application, held_keys, time
from ursina.prefabs.first_person_controller import FirstPersonController

from core.documents import DocumentFormatError, load_documents
from core.facility import Facility
from core.flashlight import Flashlight
from core.interactables import (
    BatteryPickup,
    ExitDoor,
    HidingSpot,
    Interactions,
    Note,
    Pickup,
    PowerPanel,
)
from core.inventory import FUSE_ITEM, PANEL_CODE
from core.level import LevelFormatError, load_level
from core.monster import Monster
from core.player import Player
from core.session import GameSession, GameStatus
from core.stamina import Stamina
from view.coords import cell_to_world, world_to_cell
from view.game_audio import AudioState, GameAudio
from view.hud import Hud
from view.level_renderer import WALL_HEIGHT, LevelRenderer
from view.lighting import Lighting
from view.monster_view import MonsterView

LEVEL_PATH = "levels/level1.txt"
DOCUMENTS_PATH = "levels/level1_documents.txt"
MOUSE_SENSITIVITY = Vec2(25, 25)

FLASHLIGHT_CAPACITY = 100
FLASHLIGHT_DRAIN_PER_SECOND = 2    # batterie pleine = 50 secondes d'éclairage
BATTERY_CHARGE = 40                # une pile recharge 40 % de la batterie

WALK_SPEED = 3
RUN_SPEED = 6
STAMINA_CAPACITY = 100
STAMINA_DRAIN_PER_SECOND = 25      # 4 secondes de course à fond
STAMINA_REGEN_PER_SECOND = 12      # environ 8 secondes pour se recharger

MONSTER_PATROL_SPEED = 2           # il rôde, plus lent que votre marche
MONSTER_CHASE_SPEED = 4            # il fonce : seule la course permet de le distancer
MONSTER_GRACE_PERIOD = 20          # secondes avant qu'il ne commence à bouger
PEACEFUL_MODE = False              # True pour tester sans le monstre
CATCH_DISTANCE = 0.9
MONSTER_PATROL = [(14, 26), (7, 22), (11, 15), (12, 4), (7, 8), (2, 26)]

CODE_NOTE_TITLE = "Note de Daniel Morel"
CODE_NOTE_TEXT = (
    "Si tu lis ça, le courant a sauté et les portes du B sont ouvertes.\n"
    "Il y a un fusible de rechange dans la réserve. Code du tableau : 4 7 1.\n"
    "Ne cours pas sauf si tu y es obligé. Il entend.\n"
    "Rends ton badge à l'heure.\n"
    "— D. M."
)
DEFEAT_TEXT = "Le poste de gardien de nuit est à nouveau vacant."


class GameController(Entity):
    """Traduit les touches en actions pour la session, et son état en image et en son."""

    def __init__(
        self,
        session: GameSession,
        first_person: FirstPersonController,
        monster_view: MonsterView,
        audio: GameAudio,
        renderer: LevelRenderer,
        lighting: Lighting,
        hud: Hud,
    ) -> None:
        super().__init__()
        self._session = session
        self._first_person = first_person
        self._monster_view = monster_view
        self._audio = audio
        self._renderer = renderer
        self._lighting = lighting
        self._hud = hud
        self._position_before_hiding = first_person.position
        self._end_shown = False

    def input(self, key: str) -> None:
        if self._hud.is_reading:
            if key in ("e", "escape"):
                self._close_document()
            return
        if key == "escape":
            application.quit()
        elif key == "f":
            self._toggle_flashlight()
        elif key == "e":
            self._interact()

    def update(self) -> None:
        if self._session.is_over:
            self._show_end_once()
            return
        if self._hud.is_reading:
            return   # la lecture met le jeu en pause
        is_moving = self._first_person.enabled and self._first_person.direction.length() > 0
        self._session.update(time.dt, wants_to_run=is_moving and held_keys["shift"])
        self._refresh_player_view()
        self._update_monster()
        self._update_audio(is_moving)

    def _player_cell(self):
        return world_to_cell(self._first_person.position)

    def _toggle_flashlight(self) -> None:
        was_on = self._session.player.flashlight.is_on
        self._session.toggle_flashlight()
        is_on = self._session.player.flashlight.is_on
        if is_on != was_on:
            self._audio.on_flashlight(is_on)

    def _refresh_player_view(self) -> None:
        player = self._session.player
        self._lighting.set_flashlight(player.flashlight.is_on)
        self._first_person.speed = RUN_SPEED if player.stamina.is_running else WALK_SPEED
        self._hud.show_battery(player.flashlight.charge_ratio)
        self._hud.show_stamina(player.stamina.charge_ratio, player.stamina.is_exhausted)
        item = self._session.item_near(self._player_cell())
        self._hud.show_prompt(item.prompt if item else None)
        self._hud.show_objective(self._session.objective)

    def _interact(self) -> None:
        was_hidden = self._session.player.is_hidden
        result = self._session.interact(self._player_cell())
        if result is None:
            return
        if result.item.is_readable:
            self._open_document(result.message)
        else:
            self._hud.show_message(result.message)
        if result.item.is_consumed:
            self._renderer.remove_item(result.item.cell)
            self._audio.on_pickup()
        if self._session.player.is_hidden != was_hidden:
            self._audio.on_locker()
            self._apply_hiding(result.item.cell)

    def _open_document(self, text: str) -> None:
        self._first_person.enabled = False   # on ne bouge plus pendant la lecture
        self._hud.show_document(text)

    def _close_document(self) -> None:
        self._hud.close_document()
        self._first_person.enabled = not self._session.player.is_hidden

    def _apply_hiding(self, cell) -> None:
        """Place la caméra dans le casier, ou la ressort là où le joueur est entré."""
        hidden = self._session.player.is_hidden
        if hidden:
            self._position_before_hiding = self._first_person.position
            self._first_person.position = cell_to_world(cell)
        else:
            self._first_person.position = self._position_before_hiding
        self._first_person.enabled = not hidden
        self._hud.show_hiding(hidden)

    def _monster_distance(self) -> float:
        gap = self._monster_view.position - self._first_person.position
        return Vec2(gap.x, gap.z).length()

    def _update_monster(self) -> None:
        if self._monster_view.has_arrived():
            next_cell = self._session.next_monster_cell(self._player_cell())
            if next_cell is not None:
                self._monster_view.move_to(next_cell)
                self._monster_view.set_speed(
                    MONSTER_CHASE_SPEED if self._session.monster_is_chasing
                    else MONSTER_PATROL_SPEED
                )
        self._monster_view.advance(time.dt)
        if self._monster_distance() < CATCH_DISTANCE:
            self._session.report_caught()

    def _update_audio(self, is_moving: bool) -> None:
        player = self._session.player
        self._audio.update(time.dt, AudioState(
            monster_distance=self._monster_distance(),
            monster_active=self._session.monster_is_active,
            monster_chasing=self._session.monster_is_chasing,
            monster_searching=self._session.monster_is_searching,
            player_moving=is_moving,
            player_running=player.stamina.is_running,
            player_exhausted=player.stamina.is_exhausted,
            player_hidden=player.is_hidden,
            power_on=self._session.power_on,
        ))

    def _show_end_once(self) -> None:
        if self._end_shown:
            return
        self._end_shown = True
        self._first_person.enabled = False
        won = self._session.status is GameStatus.WON
        if won:
            self._audio.on_won()
        else:
            self._audio.on_caught()
        self._hud.show_end("Vous êtes sorti." if won else DEFEAT_TEXT, won)


def build_session(level) -> GameSession:
    """Assemble le noyau : joueur, monstre, bâtiment et objets du niveau."""
    facility = Facility()
    documents = load_documents(DOCUMENTS_PATH, level)
    items = [
        Pickup(level.fuse_cell, FUSE_ITEM, "Ramasser le fusible", "Fusible de rechange récupéré."),
        Note(level.note_cell, CODE_NOTE_TITLE, CODE_NOTE_TEXT, grants=PANEL_CODE),
        PowerPanel(level.power_panel_cell, facility),
        ExitDoor(level.exit_cell, facility),
    ]
    items += [BatteryPickup(cell, BATTERY_CHARGE) for cell in level.battery_cells]
    items += [HidingSpot(cell) for cell in level.hiding_spot_cells]
    items += [Note(doc.cell, doc.title, doc.text) for doc in documents.values()]
    player = Player(
        Flashlight(FLASHLIGHT_CAPACITY, FLASHLIGHT_DRAIN_PER_SECOND),
        Stamina(STAMINA_CAPACITY, STAMINA_DRAIN_PER_SECOND, STAMINA_REGEN_PER_SECOND),
    )
    monster = Monster(level, level.monster_start, MONSTER_PATROL)
    return GameSession(
        player, monster, Interactions(items), facility,
        grace_period=MONSTER_GRACE_PERIOD, peaceful=PEACEFUL_MODE,
    )


def main() -> None:
    try:
        level = load_level(LEVEL_PATH)
        session = build_session(level)
    except (FileNotFoundError, LevelFormatError, DocumentFormatError, ValueError) as error:
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

    monster_view = MonsterView(app, level.monster_start, MONSTER_PATROL_SPEED)
    GameController(
        session, first_person, monster_view, GameAudio(app), renderer, lighting, Hud(),
    )
    app.run()


if __name__ == "__main__":
    main()