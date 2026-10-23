"""Outil : vérifier un modèle 3D (taille, orientation, rendu dans le noir).

Usage, depuis la racine du projet :
    python -m tools.preview_model assets/monster/monster.bam

Touches :
    R            pivoter de 90° autour de l'axe gauche-droite (si le modèle est couché)
    T            pivoter de 90° autour de l'axe vertical (si le modèle est de dos)
    Flèche haut  agrandir     Flèche bas  rétrécir
    F            lampe torche     Échap  quitter
    Clic droit maintenu : tourner autour du modèle.   Molette : zoomer.
"""

import sys
from pathlib import Path

from ursina import EditorCamera, Entity, Ursina, application, color

from view.lighting import Lighting, make_lit
from view.model_loader import ModelLoadError, fit_to_height, load_model

START_HEIGHT = 2.6
HEIGHT_STEP = 0.1
FLOOR_SIZE = 14


class ModelInspector(Entity):
    """Affiche un modèle et permet de régler sa taille et son orientation."""

    def __init__(self, model_node, lighting: Lighting) -> None:
        super().__init__()
        self._node = model_node
        self._node.reparentTo(self)
        self._lighting = lighting
        self._height = START_HEIGHT
        self._flashlight_on = True
        make_lit(self)
        self._refit()

    def input(self, key: str) -> None:
        if key == "r":
            self._node.setP(self._node.getP() + 90)
        elif key == "t":
            self._node.setH(self._node.getH() + 90)
        elif key == "up arrow":
            self._height += HEIGHT_STEP
        elif key == "down arrow":
            self._height = max(HEIGHT_STEP, self._height - HEIGHT_STEP)
        elif key == "f":
            self._flashlight_on = not self._flashlight_on
            self._lighting.set_flashlight(self._flashlight_on)
            return
        elif key == "escape":
            application.quit()
            return
        else:
            return
        self._refit()

    def _refit(self) -> None:
        fit_to_height(self._node, self, self._height)
        print(
            f"Hauteur : {self._height:.1f} m | "
            f"rotation R : {self._node.getP() % 360:.0f}° | "
            f"rotation T : {self._node.getH() % 360:.0f}°"
        )


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage : python -m tools.preview_model chemin/vers/modele.bam")

    app = Ursina()
    try:
        node = load_model(app, Path(sys.argv[1]))
    except ModelLoadError as error:
        sys.exit(str(error))

    make_lit(
        Entity(
            model="plane",
            scale=FLOOR_SIZE,
            texture="white_cube",
            texture_scale=(FLOOR_SIZE, FLOOR_SIZE),
            color=color.gray,
        )
    )
    EditorCamera(rotation_x=10)
    lighting = Lighting()
    lighting.setup()
    ModelInspector(node, lighting)
    app.run()


if __name__ == "__main__":
    main()
