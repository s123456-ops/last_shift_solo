"""Le volume de la musique selon le moment de la partie, et ses fondus.

N'importe pas Ursina : se teste sans fenêtre.
"""

MOODS = {  # moment → volume de la musique (0 à 1)
    "title": 0.55,  # l'écran titre installe l'angoisse
    "intro": 0.4,  # l'histoire se raconte par-dessus
    "game": 0.1,  # à peine audible : les bruits du bâtiment passent devant
    "chase": 0.03,  # presque coupée : on doit entendre le monstre arriver
    "silent": 0.0,  # fin de partie
}
FADE_PER_SECOND = 0.25  # vitesse des fondus : de 0,55 à 0,1 en moins de 2 secondes


def next_volume(current: float, target: float, dt: float) -> float:
    """Avance d'un pas vers le volume voulu, sans jamais le dépasser."""
    step = FADE_PER_SECOND * dt
    if abs(target - current) <= step:
        return target
    return current + step if target > current else current - step
