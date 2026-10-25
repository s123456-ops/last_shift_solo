"""Compose la musique d'ambiance dans assets/sounds/music/.

Usage :
    pip install numpy soundfile
    python -m tools.make_music

Un bourdonnement grave qui bat lentement, une dissonance (le triton), des
frottements métalliques qui enflent puis retombent, et un grondement sourd.
Toutes les fréquences font un nombre entier de cycles sur la durée : la boucle
se raccorde sans coupure. Rien à créditer : tout est calculé ici.
"""

from pathlib import Path

import numpy as np
import soundfile as sf

OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "sounds" / "music"
RATE = 44100
LOOP = 64.0  # secondes
SEED = 5


def looping(frequency: float) -> float:
    """La fréquence la plus proche qui boucle parfaitement sur LOOP secondes."""
    return round(frequency * LOOP) / LOOP


def tone(t: np.ndarray, frequency: float, phase: float = 0.0) -> np.ndarray:
    return np.sin(2 * np.pi * looping(frequency) * t + phase)


def swell(t: np.ndarray, period: float, sharpness: float) -> np.ndarray:
    """Une montée lente puis une retombée, qui revient tous les « period » secondes."""
    return (0.5 - 0.5 * np.cos(2 * np.pi * t / period)) ** sharpness


def low_rumble(rng: np.random.Generator, length: int) -> np.ndarray:
    """Un bruit filtré très grave : le bâtiment qui respire."""
    noise = rng.standard_normal(length)
    smooth = np.zeros(length)
    level = 0.0
    for index, value in enumerate(noise):  # filtre passe-bas d'ordre 1
        level += 0.004 * (value - level)
        smooth[index] = level
    return smooth / np.abs(smooth).max()


def channel(t: np.ndarray, rng: np.random.Generator, detune: float) -> np.ndarray:
    drone = 0.5 * tone(t, 55.0) + 0.5 * tone(t, 55.0 + 0.3 + detune)  # battement lent
    fifth = 0.18 * tone(t, 82.4 + detune)
    tritone = 0.10 * tone(t, 77.8, phase=1.0) * swell(t, 16.0, 2)  # la note qui dérange
    metal = (0.05 * tone(t, 1760.0 + detune * 10) + 0.04 * tone(t, 1867.0)) * swell(
        t, 21.333, 6
    )  # frottement d'archet sur du métal
    rumble = 0.35 * low_rumble(rng, len(t)) * swell(t, 32.0, 1)
    breathing = 0.75 + 0.25 * np.sin(2 * np.pi * t / 8.0)  # le tout respire
    return (drone + fifth + tritone) * breathing + metal + rumble


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    t = np.arange(int(RATE * LOOP)) / RATE
    stereo = np.stack([channel(t, rng, -0.1), channel(t, rng, 0.1)], axis=1)
    stereo *= 0.7 / np.abs(stereo).max()  # marge pour éviter la saturation
    path = OUTPUT / "musique_menace.ogg"
    with sf.SoundFile(path, "w", RATE, 2, format="OGG", subtype="VORBIS") as file:
        for start in range(0, len(stereo), RATE):  # par morceaux d'une seconde :
            file.write(stereo[start : start + RATE])  # d'un bloc, l'encodeur plante
    print(f"Musique créée : {path.name} ({LOOP:.0f} s, en boucle)")


if __name__ == "__main__":
    main()
