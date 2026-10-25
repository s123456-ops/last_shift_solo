"""THE LAST SHIFT, version solo : point d'entrée du jeu.

Usage :
    python main.py              (anglais, par défaut)
    python main.py --lang fr    (français)
"""

import argparse
import sys

from ursina import Entity, Ursina, Vec2, application, color, held_keys, time, window
from ursina.prefabs.first_person_controller import FirstPersonController

from core.difficulty import DIFFICULTIES, NORMAL, Difficulty
from core.documents import DocumentFormatError, load_documents
from core.doors import MapWithDoors
from core.facility import Facility
from core.flashlight import Flashlight
from core.interactables import (
    BatteryPickup,
    ExitDoor,
    HidingSpot,
    Interactions,
    LockedDoor,
    Note,
    Pickup,
    PowerPanel,
)
from core.inventory import CODE_END, CODE_START, FUSE_ITEM, KEYCARD_ITEM
from core.level import LevelFormatError, load_level
from core.monster import Monster
from core.player import Player
from core.session import GameSession, GameStatus
from core.stamina import Stamina
from core.texts import SUPPORTED_LANGUAGES, current_language, set_language, tr
from view.coords import cell_to_world, world_to_cell
from view.game_audio import AudioState, GameAudio, set_master_volume
from view.hud import Hud
from view.level_renderer import WALL_HEIGHT, LevelRenderer
from view.lighting import Lighting
from view.map_screen import MapScreen
from view.monster_view import MonsterView
from view.pause_menu import PauseMenu
from view.screens import IntroSequence, TitleScreen
from view.settings import PlayerSettings, Setting, default_settings
from view.title_backdrop import TitleBackdrop

GAME_LANGUAGE = "en"
LEVEL_PATH = "levels/level1.txt"
DOCUMENTS_PATH = "levels/level1_documents.{language}.txt"

FLASHLIGHT_CAPACITY = 100
BATTERY_CHARGE = 40  # une pile recharge 40 % de la batterie

WALK_SPEED = 3
RUN_SPEED = 6
STAMINA_CAPACITY = 100
STAMINA_DRAIN_PER_SECOND = 25  # 4 secondes de course à fond
STAMINA_REGEN_PER_SECOND = 12  # environ 8 secondes pour se recharger

CATCH_DISTANCE = 0.9
START_INPUT_GRACE = 0.5  # secondes : la touche qui a fermé l'intro est ignorée
MONSTER_PATROL = [
    (14, 26),  # sa salle de départ
    (7, 22),
    (8, 40),  # couloir de l'aile C
    (13, 37),  # laboratoire
    (21, 37),  # quai de chargement
    (18, 20),  # couloir de service
    (12, 4),  # salle de maintenance
    (7, 8),
    (2, 15),
]
CODE_END_DOCUMENT = (15, 28)  # le journal de Daniel Morel donne le dernier chiffre

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
        map_screen: MapScreen,
        settings: PlayerSettings,
        difficulty: Difficulty,
    ) -> None:
        super().__init__()
        self._session = session
        self._first_person = first_person
        self._monster_view = monster_view
        self._audio = audio
        self._renderer = renderer
        self._lighting = lighting
        self._hud = hud
        self._map = map_screen
        self._difficulty = difficulty
        self._position_before_hiding = first_person.position
        self._end_shown = False
        self._paused = False
        self._pause_menu = PauseMenu(
            settings, on_resume=self._toggle_pause, on_quit=application.quit
        )
        self._input_grace = START_INPUT_GRACE

    def input(self, key: str) -> None:
        if self._session.is_over:
            if key == "escape":
                application.quit()
            return
        if self._input_grace > 0:
            return
        if self._paused:
            if key == "escape":
                self._toggle_pause()
            elif key == "q":
                application.quit()
            return
        if self._hud.is_reading:
            if key in ("e", "escape"):
                self._close_document()
            return
        if self._map.is_open:
            if key in ("m", "escape"):
                self._toggle_map()
            return
        if key == "escape":
            self._toggle_pause()
        elif key == "f":
            self._toggle_flashlight()
        elif key == "e":
            self._interact()
        elif key == "m":
            self._toggle_map()

    def update(self) -> None:
        self._input_grace = max(0.0, self._input_grace - time.dt)
        if self._session.is_over:
            self._show_end_once()
            return
        if self._paused or self._hud.is_reading or self._map.is_open:
            return  # la pause, la lecture et le plan figent le jeu
        is_moving = (
            self._first_person.enabled and self._first_person.direction.length() > 0
        )
        self._session.update(time.dt, wants_to_run=is_moving and held_keys["shift"])
        self._refresh_player_view()
        self._update_monster()
        self._update_audio(is_moving)

    def _toggle_pause(self) -> None:
        """Fige la partie ; le contrôleur du joueur libère ou capture la souris."""
        self._paused = not self._paused
        self._map.close()
        self._first_person.enabled = (
            not self._paused and not self._session.player.is_hidden
        )
        self._hud.show_prompt(None)
        self._pause_menu.show(self._paused)

    def _toggle_map(self) -> None:
        """Ouvre ou ferme le plan. Le jeu est figé tant qu'il est ouvert."""
        self._map.toggle()
        if self._map.is_open:
            self._map.show_player(self._first_person.position)
        self._first_person.enabled = (
            not self._map.is_open and not self._session.player.is_hidden
        )

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
        self._map.close()
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
                    self._difficulty.monster_chase_speed
                    if self._session.monster_is_chasing
                    else self._difficulty.monster_patrol_speed
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
        self._map.close()
        self._first_person.enabled = False
        won = self._session.status is GameStatus.WON
        if won:
            self._audio.on_won()
        else:
            self._audio.on_caught()
        self._hud.show_end(tr("end.won") if won else tr("end.lost"), won)


def build_session(
    level, language: str, peaceful: bool, difficulty: Difficulty
) -> GameSession:
    """Assemble le noyau : joueur, monstre, bâtiment et objets du niveau."""
    facility = Facility()
    documents = load_documents(DOCUMENTS_PATH.format(language=language), level)
    doors = [LockedDoor(cell) for cell in level.security_door_cells]
    items = [
        Pickup(level.fuse_cell, FUSE_ITEM, tr("fuse.prompt"), tr("fuse.message")),
        Note(
            level.note_cell,
            tr("code_note.title"),
            tr("code_note.text"),
            grants=CODE_START,
        ),
        PowerPanel(level.power_panel_cell, facility),
        ExitDoor(level.exit_cell, facility),
    ]
    items += [BatteryPickup(cell, BATTERY_CHARGE) for cell in level.battery_cells]
    items += [HidingSpot(cell) for cell in level.hiding_spot_cells]
    if CODE_END_DOCUMENT not in documents:
        raise ValueError(
            f"Aucun document en {CODE_END_DOCUMENT} : le code serait incomplet."
        )
    items += [
        Note(
            doc.cell,
            doc.title,
            doc.text,
            grants=CODE_END if doc.cell == CODE_END_DOCUMENT else None,
        )
        for doc in documents.values()
    ]
    items += doors
    if level.keycard_cell is not None:
        items.append(
            Pickup(
                level.keycard_cell,
                KEYCARD_ITEM,
                tr("keycard.prompt"),
                tr("keycard.message"),
            )
        )
    player = Player(
        Flashlight(FLASHLIGHT_CAPACITY, difficulty.flashlight_drain),
        Stamina(STAMINA_CAPACITY, STAMINA_DRAIN_PER_SECOND, STAMINA_REGEN_PER_SECOND),
    )
    monster = Monster(
        MapWithDoors(level, doors),
        level.monster_start,
        MONSTER_PATROL,
        hearing_range=difficulty.monster_hearing,
    )
    return GameSession(
        player,
        monster,
        Interactions(items),
        facility,
        grace_period=difficulty.grace_period,
        peaceful=peaceful,
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
    app,
    level,
    session: GameSession,
    renderer: LevelRenderer,
    lighting: Lighting,
    settings: PlayerSettings,
    difficulty: Difficulty,
) -> None:
    """Place le joueur et le monstre, puis lance la partie."""
    first_person = FirstPersonController(position=cell_to_world(level.player_start))

    def apply_sensitivity(value: float) -> None:
        first_person.mouse_sensitivity = Vec2(value, value)

    settings.sensitivity.bind(apply_sensitivity)
    monster_view = MonsterView(
        app, level.monster_start, difficulty.monster_patrol_speed
    )
    GameController(
        session,
        first_person,
        monster_view,
        GameAudio(app),
        renderer,
        lighting,
        Hud(),
        MapScreen(level, difficulty),
        settings,
        difficulty,
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
    language = parse_arguments().lang
    try:
        set_language(language)
        level = load_level(LEVEL_PATH)
        # on assemble une première partie pour vérifier les fichiers
        # avant d'ouvrir la fenêtre ; la vraie est créée après le choix du mode
        build_session(level, language, peaceful=False, difficulty=NORMAL)
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
    settings = default_settings()
    settings.brightness.bind(lighting.set_brightness)
    settings.volume.bind(lambda volume: set_master_volume(app, volume))
    difficulty = Setting(
        "options.difficulty",
        tuple((choice.name_key, choice) for choice in DIFFICULTIES),
        default=DIFFICULTIES.index(NORMAL),
    )
    backdrop = TitleBackdrop(
        app, TITLE_CAMERA_START, TITLE_CAMERA_END, TITLE_SILHOUETTE
    )

    def begin(peaceful: bool) -> None:
        backdrop.stop()
        chosen = difficulty.value
        session = build_session(level, current_language(), peaceful, chosen)
        IntroSequence(
            on_finish=lambda: start_game(
                app, level, session, renderer, lighting, settings, chosen
            )
        )

    TitleScreen(on_start=begin, brightness=settings.brightness, difficulty=difficulty)
    app.run()


if __name__ == "__main__":
    main()
