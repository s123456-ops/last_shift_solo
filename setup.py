"""Builds THE LAST SHIFT as a standalone game, with Panda3D's build_apps.

Usage (on Windows, from the project root, inside the virtual environment):
    pip install -r requirements.txt
    python setup.py bdist_apps

The result is dist/THE_LAST_SHIFT-<version>_win_amd64.zip: unzip it anywhere and
double-click "THE LAST SHIFT.exe". Players need nothing else installed.
"""

from setuptools import setup

VERSION = "0.1.2"

setup(
    name="THE_LAST_SHIFT",
    version=VERSION,
    options={
        "build_apps": {
            # a game window, without a console behind it
            "gui_apps": {"THE LAST SHIFT": "main.py"},
            # the same game with a console window, to read errors on a tester's PC
            "console_apps": {"THE LAST SHIFT (debug)": "main.py"},
            # the game's data files, copied next to the executable
            "include_patterns": [
                "levels/*.txt",
                "locales/*.json",
                "assets/monster/*.bam",
                "assets/models/*.bam",
                "assets/sounds/**/*.ogg",
                "assets/sounds/**/*.wav",
                "assets/textures/*.png",
                "CREDITS.md",
            ],
            # Ursina's own models, fonts and textures (cube, quad, default font...)
            "package_data_dirs": {
                "ursina": [
                    ("ursina/models_compressed/*", "ursina/models_compressed", {}),
                    ("ursina/fonts/*", "ursina/fonts", {}),
                    ("ursina/textures/*", "ursina/textures", {}),
                    ("ursina/audio/*", "ursina/audio", {}),
                ],
            },
            # only what the game needs at runtime (no pytest, no ruff)
            "requirements_path": "requirements-game.txt",
            "plugins": ["pandagl", "p3openal_audio"],
            "platforms": ["win_amd64"],
        }
    },
)
