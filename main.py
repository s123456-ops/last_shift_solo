"""THE LAST SHIFT, version solo : point d'entrée du jeu.

Usage :
    python main.py              (anglais, par défaut)
    python main.py --lang fr    (français)
"""

import argparse
import sys

from ursina import Entity, Ursina, Vec2, application, color, held_keys, time, window
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
from core.texts import SUPPORTED_LANGUAGES, set_language, tr
from view.coords import cell_to_world, world_to_cell
from view.game_audio import AudioState, GameAudio
from view.hud import Hud
from view.level_renderer import WALL_HEIGHT, LevelRenderer
from view.lighting import Lighting
from view.monster_view import MonsterView
from view.screens import IntroSequence, TitleScreen
from view.title_backdrop import TitleBackdrop

GAME_LANGUAGE = "en"
LEVEL_PATH = "levels/level1.txt"
DOCUMENTS_PATH = "levels/level1_documents.{language}.txt"
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

TITLE_CAMERA_START = (7, 2)  # début du couloir principal, à l'ouest
TITLE_CAMERA_END = (7, 18)  # la caméra s'arrête avant d'atteindre la silhouette
TITLE_SILHOUETTE = (7, 27)  # le monstre, au fond, près d'une lumière de secours


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
            return  # la lecture met le jeu en pause
        is_moving = (
            self._first_person.enabled and self._first_person.direction.length() > 0
        )
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
        self._first_person.speed = (
            RUN_SPEED if player.stamina.is_running else WALK_SPEED
        )
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
        self._first_person.enabled = False  # on ne bouge plus pendant la lecture
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
                    MONSTER_CHASE_SPEED
                    if self._session.monster_is_chasing
                    else MONSTER_PATROL_SPEED
                )
        self._monster_view.advance(time.dt)
        if self._monster_distance() < CATCH_DISTANCE:
            self._session.report_caught()

    def _update_audio(self, is_moving: bool) -> None:
        player = self._session.player
        self._audio.update(
            time.dt,
            AudioState(
                monster_distance=self._monster_distance(),
                monster_active=self._session.monster_is_active,
                monster_chasing=self._session.monster_is_chasing,
                monster_searching=self._session.monster_is_searching,
                player_moving=is_moving,
                player_running=player.stamina.is_running,
                player_exhausted=player.stamina.is_exhausted,
                player_hidden=player.is_hidden,
                power_on=self._session.power_on,
            ),
        )

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
        self._hud.show_end(tr("end.won") if won else tr("end.lost"), won)


def build_session(level, language: str) -> GameSession:
    """Assemble le noyau : joueur, monstre, bâtiment et objets du niveau."""
    facility = Facility()
    documents = load_documents(DOCUMENTS_PATH.format(language=language), level)
    items = [
        Pickup(level.fuse_cell, FUSE_ITEM, tr("fuse.prompt"), tr("fuse.message")),
        Note(
            level.note_cell,
            tr("code_note.title"),
            tr("code_note.text"),
            grants=PANEL_CODE,
        ),
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
        player,
        monster,
        Interactions(items),
        facility,
        grace_period=MONSTER_GRACE_PERIOD,
        peaceful=PEACEFUL_MODE,
    )


def build_world(level) -> tuple[LevelRenderer, Lighting]:
    """Le décor et l'éclairage, partagés par l'écran titre et la partie."""
    renderer = LevelRenderer(level)
    renderer.build()
    lighting = Lighting()
    lighting.setup()
    lighting.add_emergency_lights(level.emergency_light_cells, WALL_HEIGHT)
    lighting.add_exit_light(level.exit_cell, WALL_HEIGHT)
    return renderer, lighting


def start_game(
    app, level, session: GameSession, renderer: LevelRenderer, lighting: Lighting
) -> None:
    """Place le joueur et le monstre, puis lance la partie."""
    first_person = FirstPersonController(position=cell_to_world(level.player_start))
    first_person.mouse_sensitivity = MOUSE_SENSITIVITY
    monster_view = MonsterView(app, level.monster_start, MONSTER_PATROL_SPEED)
    GameController(
        session,
        first_person,
        monster_view,
        GameAudio(app),
        renderer,
        lighting,
        Hud(),
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="THE LAST SHIFT")
    parser.add_argument(
        "--lang",
        choices=SUPPORTED_LANGUAGES,
        default=GAME_LANGUAGE,
        help=f"langue du jeu (par défaut : {GAME_LANGUAGE})",
    )
    return parser.parse_args()


def main() -> None:
    import traceback  # --- diagnostic temporaire, à retirer ensuite ---

    real_exit = sys.exit

    def traced_exit(*args):
        print("\n=== QUELQU'UN QUITTE LE JEU, DEPUIS : ===")
        traceback.print_stack()
        real_exit(*args)

    sys.exit = traced_exit
    # --- fin du diagnostic ---

    language = parse_arguments().lang

    language = parse_arguments().lang
    try:
        set_language(language)
        level = load_level(LEVEL_PATH)
        session = build_session(level, language)
    except (
        FileNotFoundError,
        LevelFormatError,
        DocumentFormatError,
        ValueError,
    ) as error:
        sys.exit(f"Impossible de préparer la partie : {error}")

    app = Ursina()
    window.color = color.black
    renderer, lighting = build_world(level)
    backdrop = TitleBackdrop(
        app, TITLE_CAMERA_START, TITLE_CAMERA_END, TITLE_SILHOUETTE
    )

    def begin() -> None:
        backdrop.stop()
        IntroSequence(
            on_finish=lambda: start_game(app, level, session, renderer, lighting)
        )

    TitleScreen(on_start=begin)
    app.run()


if __name__ == "__main__":
    main()
