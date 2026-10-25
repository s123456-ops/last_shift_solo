"""Tool: check that the game can play a sound file.

Usage: python -m tools.test_sound assets/sounds/monster/monster_scream.ogg
"""

import sys
from pathlib import Path

from panda3d.core import AudioSound, Filename
from ursina import Text, Ursina, application, camera


def main() -> None:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("assets/sounds/monster/monster_scream.ogg")
    )
    print("Dossier courant :", Path.cwd())
    print("File found:", path.is_file(), "->", path.resolve())
    app = Ursina()
    print("Gestionnaires audio :", len(app.sfxManagerList), "| actif :", app.sfxActive)
    sound = app.loader.loadSfx(Filename.fromOsSpecific(str(path.resolve())))
    print("Duration read by Panda3D:", round(sound.length(), 2), "s")
    sound.setVolume(1.0)
    sound.play()
    print(
        "Status after play:",
        "EN LECTURE" if sound.status() == AudioSound.PLAYING else sound.status(),
    )
    Text("[Space] replay   [Esc] quit", parent=camera.ui, origin=(0, 0))

    def input(key):
        if key == "space":
            sound.play()
        elif key == "escape":
            application.quit()

    app.input = input
    import __main__

    __main__.input = input
    app.run()


if __name__ == "__main__":
    main()
