# THE LAST SHIFT

A first-person horror game in Python, with a PS1 look.

*Helix Institute, Sector B. Closed for six years. You are the new night watchman,
and the power just went out. Something that used to work here is still walking
the corridors.*

Restore the power and reach the exit before it finds you: find the fuse, piece
together the generator code, open the security doors, and hide in the lockers
when you hear it coming.

This repository is the **solo version** of a group project for the *Clean Code*
course (Master 2 Big Data, Business Intelligence & Analytics, Université Sorbonne
Paris Nord). It focuses on readable, tested, object-oriented Python.

## Features

- **A 45 × 25 building** with ten rooms, regular doors you can close behind you,
  security doors that need a keycard, lockers to hide in, and an evacuation plan (M).
- **A monster with three states** (patrol, chase, search) that sees with your
  flashlight, hears you run, and walks around furniture and closed doors.
- **Two modes**: *Exploration* (no monster) and *Survival*.
- **Three difficulty levels**: monster speed, hearing, delay before it starts
  moving, flashlight battery, hints on the plan; in *hard*, it opens doors itself.
- **PS1 horror style**: low resolution, reduced colours and dithering, as a shader
  that can be switched off.
- **Atmosphere**: 3D positional sound, head bob, a flashlight held in hand,
  damaged walls, debris, fallen ceiling tiles, furniture, signs, ambient music.
- **English and French**, chosen on the title screen.
- **Options** at any time: brightness, volume, mouse sensitivity, PS1 style.

## Requirements and installation

Python 3.13 and a graphics card that supports OpenGL 3.2.

```bash
git clone https://github.com/s123456-ops/last_shift_solo.git
cd last_shift_solo
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

## Running the game

```bash
python main.py              # English
python main.py --lang fr    # French
```

| Key | Action |
| --- | --- |
| W A S D | move |
| Shift | run (drains stamina, and the monster hears it) |
| Mouse | look around |
| F | flashlight on / off |
| E | interact: pick up, read, open, hide |
| M | evacuation plan (pauses the game) |
| Esc | pause menu and options |

## Running the tests

```bash
python -m pytest     # 187 tests, about one second
ruff check .
ruff format .
```

The tests never open a window: every rule of the game lives in `core/`, which
does not import the game engine.

## Project structure

```
core/       game rules, engine-independent and fully tested
view/       display and sound with Ursina; decides nothing
levels/     the level as text files: map, documents, signs, furniture
locales/    every displayed text, in English and French
assets/     models, sounds and textures
tools/      scripts that generate textures, signs, sounds and music
tests/      pytest suite
main.py     entry point: assembles the core and the view
```

## Design choices

- **The core decides, the view shows.** `GameSession` holds the rules; the view
  only asks it questions. The engine could be replaced without touching a single
  rule or test.
- **Polymorphism instead of conditions.** Every interactive object (`BatteryPickup`,
  `HidingSpot`, `Note`, `PowerPanel`, `LockedDoor`, `Door`, `ExitDoor`…) inherits
  from `Interactable`. The session calls `interact()` without ever checking the type.
- **Data instead of `if` chains.** Difficulty levels, object styles, settings,
  music volumes and furniture are objects or tables. Adding a *nightmare* mode
  means adding one object.
- **Composable maps.** The monster receives `MapWithDoors(MapWithFurniture(level))`:
  each wrapper adds obstacles without changing the original map, and the monster
  only ever calls `is_wall()`.
- **Validated level files.** The map, documents, signs and furniture are text
  files, each with its own parser that rejects mistakes with a clear message.
- **State pattern** for the monster, **facade** for the audio, **dependency
  injection** for the pathfinder and random generators.

## Editing the level

| File | Content |
| --- | --- |
| `levels/level1.txt` | the map: `#` wall, `P` player, `M` monster, `E` exit, `F` fuse, `G` generator, `N` note, `K` keycard, `S` security door, `O` door, `B` battery, `D` document, `H` locker, `L` emergency light |
| `levels/level1_documents.en.txt` | documents to read, one per `D` cell (also `.fr.txt`) |
| `levels/level1_signs.txt` | wall signs: `row column direction key` |
| `levels/level1_props.txt` | furniture: `row column kind direction` |

`tests/test_shipped_level.py` checks that the level stays playable after any change.

## Regenerating the assets

```bash
python -m tools.make_textures      # walls, floor, ceiling, damage, debris
python -m tools.make_signs         # wall signs, from locales/
python -m tools.import_textures    # object textures, from assets/textures/source/
python -m tools.make_sounds        # water drips
pip install numpy soundfile
python -m tools.make_music         # ambient music
```

## Credits

See [CREDITS.md](CREDITS.md).
