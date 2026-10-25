"""Where the game's files are, whichever folder the game is launched from.

Engine-independent module.
"""

import sys
from pathlib import Path


def game_root() -> Path:
    """The folder that holds levels/, locales/ and assets/.

    In a packaged build, the files sit next to the executable; otherwise, they
    sit next to this project's main.py, one level above core/.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


ROOT = game_root()


def resource(*parts: str) -> Path:
    """An absolute path to one of the game's files, e.g. resource("levels", "level1.txt")."""
    return ROOT.joinpath(*parts)
