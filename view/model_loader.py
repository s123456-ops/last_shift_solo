"""Chargement des modèles 3D, mise à l'échelle et réglages des modèles du jeu."""

from dataclasses import dataclass
from pathlib import Path

from panda3d.core import Filename, NodePath
from ursina import Entity

from view.lighting import make_lit


class ModelLoadError(Exception):
    """Un fichier de modèle 3D est absent ou illisible."""


@dataclass(frozen=True)
class ModelSpec:
    """Un modèle et ses réglages, trouvés avec tools/preview_model.py."""

    path: Path
    height: float  # hauteur en mètres
    pitch: float = 0.0  # rotation R de l'outil
    heading: float = 0.0  # rotation T de l'outil


MONSTER = ModelSpec(
    Path("assets/monster/monster.bam"), height=2.6, pitch=90, heading=180
)
GENERATOR = ModelSpec(Path("assets/models/generator.bam"), height=0.85, pitch=90)
EXIT_DOOR = ModelSpec(Path("assets/models/exit_door.bam"), height=2.3, pitch=90)


def load_model(app, path: Path) -> NodePath:
    """Charge un fichier 3D avec le chargeur de Panda3D."""
    if not path.is_file():
        raise ModelLoadError(f"Modèle introuvable : {path}")
    try:
        node = app.loader.loadModel(Filename.fromOsSpecific(str(path.resolve())))
    except OSError as error:
        raise ModelLoadError(
            f"Impossible de charger le modèle {path} : {error}"
        ) from error
    if node is None:
        raise ModelLoadError(f"Impossible de charger le modèle {path}.")
    return node


def fit_to_height(node: NodePath, reference: NodePath, height: float) -> None:
    """Met le modèle à la hauteur voulue, centré et posé sur le sol (y = 0 dans Ursina)."""
    node.setPos(0, 0, 0)
    node.setScale(1)
    low, high = node.getTightBounds(reference)
    factor = height / (high.y - low.y)
    node.setScale(factor)
    node.setPos(
        -(low.x + high.x) / 2 * factor,
        -low.y * factor,
        -(low.z + high.z) / 2 * factor,
    )


def place_model(app, spec: ModelSpec, holder: Entity) -> NodePath:
    """Charge un modèle, lui applique ses réglages et l'attache à une entité."""
    node = load_model(app, spec.path)
    node.reparentTo(holder)
    node.setHpr(spec.heading, spec.pitch, 0)
    fit_to_height(node, holder, spec.height)
    make_lit(holder)
    return node
