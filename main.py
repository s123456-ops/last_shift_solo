"""THE LAST SHIFT, solo version: game entry point.

Usage:
    python main.py              (English, default)
    python main.py --lang fr    (French)
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
    Door,
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
from core.props import MapWithFurniture, PropFormatError, load_props
from core.session import GameSession, GameStatus
from core.signs import SignFormatError, load_signs
from core.stamina import Stamina
from core.texts import SUPPORTED_LANGUAGES, current_language, set_language, tr
from view.camera_motion import HeadBob
from view.coords import cell_to_world, world_to_cell
from view.game_audio import AudioState, GameAudio, set_master_volume
from view.hud import Hud
from view.level_renderer import WALL_HEIGHT, LevelRenderer
from view.lighting import Lighting
from view.map_screen import MapScreen
from view.monster_view import MonsterView
from view.music import Music
from view.pause_menu import PauseMenu
from view.retro import set_retro_style
from view.screens import IntroSequence, TitleScreen
from view.settings import PlayerSettings, Setting, default_settings
from view.title_backdrop import TitleBackdrop

GAME_LANGUAGE = "en"
LEVEL_PATH = "levels/level1.txt"
DOCUMENTS_PATH = "levels/level1_documents.{language}.txt"
SIGNS_PATH = "levels/level1_signs.txt"
PROPS_PATH = "levels/level1_props.txt"

FLASHLIGHT_CAPACITY = 100
BATTERY_CHARGE = 40  # a battery recharges 40 % of the flashlight

WALK_SPEED = 3
RUN_SPEED = 6
STAMINA_CAPACITY = 100
STAMINA_DRAIN_PER_SECOND = 25  # 4 seconds of full sprint
STAMINA_REGEN_PER_SECOND = 12  # about 8 seconds to recover

CATCH_DISTANCE = 0.9
START_INPUT_GRACE = 0.5  # seconds: the key that closed the intro is ignored
MONSTER_PATROL = [
    (14, 26),  # its starting room
    (7, 22),
    (8, 40),  # couloir de l'aile C
    (13, 37),  # laboratoire
    (21, 37),  # quai de chargement
    (18, 20),  # couloir de service
    (12, 4),  # salle de maintenance
    (7, 8),
    (2, 15),
]
CODE_END_DOCUMENT = (15, 28)  # Daniel Morel's journal gives the last digit

TITLE_CAMERA_START = (7, 2)  # start of the main corridor, to the west
TITLE_CAMERA_END = (7, 18)  # the camera stops before reaching the silhouette
TITLE_SILHOUETTE = (7, 27)  # the monster, at the far end, near an emergency light


class GameController(Entity):
    """Turns key presses into actions for the session, and its state into images and sound."""

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
        music: Music,
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
        self._music = music
        music.set_mood("game")
        self._position_before_hiding = first_person.position
        self._end_shown = False
        self._paused = False
        self._pause_menu = PauseMenu(
            settings, on_resume=self._toggle_pause, on_quit=application.quit
        )
        self._input_grace = START_INPUT_GRACE
        self._head_bob = HeadBob()
        self._eye_height = first_person.camera_pivot.y

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
            return  # pause, reading and the map freeze the game
        is_moving = (
            self._first_person.enabled and self._first_person.direction.length() > 0
        )
        self._session.update(time.dt, wants_to_run=is_moving and held_keys["shift"])
        self._refresh_player_view()
        self._move_head(is_moving)
        for _ in self._renderer.sync_doors(self._session.doors):
            self._audio.on_locker()  # metallic creak of a moving door
        self._update_monster()
        self._update_audio(is_moving)
        self._music.set_mood("chase" if self._session.monster_is_chasing else "game")

    def _move_head(self, is_moving: bool) -> None:
        """Head bob while walking, flashlight shaking when out of breath."""
        stamina = self._session.player.stamina
        vertical, sideways = self._head_bob.update(
            time.dt, is_moving, stamina.is_running
        )
        self._first_person.camera_pivot.y = self._eye_height + vertical
        self._first_person.camera_pivot.x = sideways
        self._lighting.set_trembling(stamina.is_exhausted)

    def _toggle_pause(self) -> None:
        """Freezes the game; the player controller releases or captures the mouse."""
        self._paused = not self._paused
        self._map.close()
        self._first_person.enabled = (
            not self._paused and not self._session.player.is_hidden
        )
        self._hud.show_prompt(None)
        self._pause_menu.show(self._paused)

    def _toggle_map(self) -> None:
        """Opens or closes the map. The game is frozen while it is open."""
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
        elif result.message:
            self._hud.show_message(result.message)
        if result.item.is_consumed:
            self._renderer.remove_item(result.item.cell)
            self._audio.on_pickup()
        if self._session.player.is_hidden != was_hidden:
            self._audio.on_locker()
            self._apply_hiding(result.item.cell)

    def _open_document(self, text: str) -> None:
        self._map.close()
        self._first_person.enabled = False  # the player cannot move while reading
        self._hud.show_document(text)

    def _close_document(self) -> None:
        self._hud.close_document()
        self._first_person.enabled = not self._session.player.is_hidden

    def _apply_hiding(self, cell) -> None:
        """Puts the camera inside the locker, or back where the player got in."""
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
        self._music.set_mood("silent")
        self._map.close()
        self._first_person.enabled = False
        won = self._session.status is GameStatus.WON
        if won:
            self._audio.on_won()
        else:
            self._audio.on_caught()
        self._hud.show_end(tr("end.won") if won else tr("end.lost"), won)


def build_session(
    level, language: str, peaceful: bool, difficulty: Difficulty, props=()
) -> GameSession:
    """Assembles the core: player, monster, building and the level's objects."""
    facility = Facility()
    documents = load_documents(DOCUMENTS_PATH.format(language=language), level)
    security_doors = [LockedDoor(cell) for cell in level.security_door_cells]
    doors = [Door(cell) for cell in level.door_cells]
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
            f"No document at {CODE_END_DOCUMENT}: the code would be incomplete."
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
    items += security_doors + doors
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
    # Security doors always stop the monster; regular doors,
    # only when it cannot open them (easy and normal).
    barriers = security_doors + ([] if difficulty.monster_opens_doors else doors)
    monster = Monster(
        MapWithDoors(MapWithFurniture(level, props), barriers),
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
        doors=doors,
        monster_opens_doors=difficulty.monster_opens_doors,
    )


def build_world(app, level, signs, props) -> tuple[LevelRenderer, Lighting]:
    """The scenery and lighting, shared by the title screen and the game."""
    renderer = LevelRenderer(level, app=app, signs=signs, props=props)
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
    music: Music,
) -> None:
    """Places the player and the monster, then starts the game."""
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
        GameAudio(app, monster_view.entity, renderer.water_points),
        renderer,
        lighting,
        Hud(),
        MapScreen(level, difficulty),
        settings,
        difficulty,
        music,
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="THE LAST SHIFT")
    parser.add_argument(
        "--lang",
        choices=SUPPORTED_LANGUAGES,
        default=GAME_LANGUAGE,
        help=f"game language (default: {GAME_LANGUAGE})",
    )
    return parser.parse_args()


def main() -> None:
    language = parse_arguments().lang
    try:
        set_language(language)
        level = load_level(LEVEL_PATH)
        # a first game is assembled to check the files
        # before opening the window; the real one is created once the mode is chosen
        signs = load_signs(SIGNS_PATH, level)
        props = load_props(PROPS_PATH, level)
        build_session(level, language, peaceful=False, difficulty=NORMAL, props=props)
    except (
        FileNotFoundError,
        LevelFormatError,
        DocumentFormatError,
        SignFormatError,
        PropFormatError,
        ValueError,
    ) as error:
        sys.exit(f"Could not prepare the game: {error}")

    app = Ursina()
    window.color = color.black
    renderer, lighting = build_world(app, level, signs, props)
    settings = default_settings()
    settings.brightness.bind(lighting.set_brightness)
    settings.volume.bind(lambda volume: set_master_volume(app, volume))
    settings.retro.bind(set_retro_style)
    music = Music(app)
    music.set_mood("title")
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
        music.set_mood("intro")
        chosen = difficulty.value
        session = build_session(level, current_language(), peaceful, chosen, props)
        IntroSequence(
            on_finish=lambda: start_game(
                app, level, session, renderer, lighting, settings, chosen, music
            )
        )

    TitleScreen(
        on_start=begin,
        brightness=settings.brightness,
        difficulty=difficulty,
        on_language=lambda: renderer.show_signs_in(current_language()),
    )
    app.run()


if __name__ == "__main__":
    main()
