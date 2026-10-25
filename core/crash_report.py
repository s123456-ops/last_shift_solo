"""Writes a readable report when the game crashes, where the player can find it.

Engine-independent module.
"""

import faulthandler
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

REPORT_NAME = "crash_log.txt"
NATIVE_REPORT_NAME = "native_crash_log.txt"
ENGINE_LOG_NAME = "engine_log.txt"

_native_log = None  # must stay open until the crash, so faulthandler can write in it


def write_crash_report(error: BaseException, folders: list[Path]) -> Path | None:
    """Writes the report in the first folder that accepts it; None if none does.

    The game folder comes first (next to the executable, easy to find); a
    fallback such as the user's Documents folder covers read-only installs.
    """
    report = format_report(error)
    for folder in folders:
        try:
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / REPORT_NAME
            path.write_text(report, encoding="utf-8")
            return path
        except OSError:
            continue
    return None


def format_report(error: BaseException) -> str:
    """The error, where it happened, and the player's system: all a bug report needs."""
    details = "".join(traceback.format_exception(error))
    return (
        "THE LAST SHIFT crashed. Please send this file to the developer.\n\n"
        f"Date: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"System: {platform.platform()}\n"
        f"Python: {sys.version.split()[0]}\n\n"
        f"{details}"
    )


def show_crash_message(path: Path | None) -> None:
    """A Windows message box telling the player where the report is."""
    where = str(path) if path else "(the report could not be written)"
    text = f"Sorry, THE LAST SHIFT crashed.\n\nA report was saved here:\n{where}"
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, text, "THE LAST SHIFT", 0x10)
    else:
        print(text, file=sys.stderr)

def enable_native_crash_log(folder: Path) -> Path:
    """Records crashes inside the engine (C++), which Python's try/except never sees.

    faulthandler writes the Python line that was running when the process died.
    """
    global _native_log
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / NATIVE_REPORT_NAME
    _native_log = open(path, "w", encoding="utf-8")
    faulthandler.enable(file=_native_log, all_threads=True)
    return path
