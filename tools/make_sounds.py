"""Génère les gouttes d'eau du bâtiment dans assets/sounds/ambiance/.

Usage :
    python -m tools.make_sounds

Les sons sont calculés échantillon par échantillon, sans fichier extérieur :
rien à créditer. Mono, pour que le jeu puisse les placer dans l'espace.
"""

import math
import random
import struct
import wave
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "sounds" / "ambiance"
SAMPLE_RATE = 44100
DURATION = 0.45  # secondes
SEED = 3
DROP_PITCHES = (900, 1150, 1400)  # Hz : trois gouttes un peu différentes
ECHOES = (
    (0.065, 0.30),
    (0.12, 0.15),
)  # (retard en secondes, volume) : le couloir résonne


def drop(t: float, pitch: float) -> float:
    """Le « plic » : une note qui monte très vite et s'éteint aussitôt."""
    if t < 0:
        return 0.0
    frequency = pitch * (1 + 1.2 * min(t / 0.025, 1.0))  # la note grimpe en 25 ms
    return math.sin(2 * math.pi * frequency * t) * math.exp(-t / 0.03)


def make_drip(pitch: float, rng: random.Random) -> list[float]:
    samples = []
    for index in range(int(SAMPLE_RATE * DURATION)):
        t = index / SAMPLE_RATE
        value = drop(t, pitch) + 0.35 * drop(t - 0.018, pitch * 0.7)  # petit rebond
        for delay, volume in ECHOES:
            value += volume * drop(t - delay, pitch)
        value += rng.uniform(-1, 1) * 0.004 * math.exp(-t / 0.2)  # souffle discret
        samples.append(value)
    peak = max(abs(value) for value in samples)
    return [value / peak * 0.9 for value in samples]


def save_wav(path: Path, samples: list[float]) -> None:
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)  # 16 bits
        file.setframerate(SAMPLE_RATE)
        file.writeframes(b"".join(struct.pack("<h", int(v * 32767)) for v in samples))


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    for number, pitch in enumerate(DROP_PITCHES, start=1):
        path = OUTPUT / f"goutte_{number:02d}.wav"
        save_wav(path, make_drip(pitch, rng))
        print(f"Son créé : {path.name}")


if __name__ == "__main__":
    main()
