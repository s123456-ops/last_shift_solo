"""Loading 3D models, scaling them, and the settings of the game's models."""

from dataclasses import dataclass
from pathlib import Path

from panda3d.core import Filename, NodePath
from ursina import Entity

from core.paths import resource
from view.lighting import make_lit


class ModelLoadError(Exception):
    """A 3D model file is missing or unreadable."""


@dataclass(frozen=True)
class ModelSpec:
    """A model and its settings, found with tools/preview_model.py."""

    path: Path
    height: float  # height in metres
    pitch: float = 0.0  # rotation R de l'outil
    heading: float = 0.0  # rotation T de l'outil


MONSTER = ModelSpec(
    resource("assets", "monster", "monster.bam"), height=2.6, pitch=90, heading=180
)
GENERATOR = ModelSpec(
    resource("assets", "models", "generator.bam"), height=0.85, pitch=90
)
EXIT_DOOR = ModelSpec(
    resource("assets", "models", "exit_door.bam"), height=2.3, pitch=90
)


def load_model(app, path: Path) -> NodePath:
    """Loads a 3D file with the Panda3D loader."""
    if not path.is_file():
        raise ModelLoadError(f"Model not found: {path}")
    try:
        node = app.loader.loadModel(Filename.fromOsSpecific(str(path.resolve())))
    except OSError as error:
        raise ModelLoadError(f"Could not load the model {path}: {error}") from error
    if node is None:
        raise ModelLoadError(f"Could not load the model {path}.")
    return node


def fit_to_height(node: NodePath, reference: NodePath, height: float) -> None:
    """Scales the model to the wanted height, centred and resting on the floor (y = 0 in Ursina)."""
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
    """Loads a model, applies its settings and attaches it to an entity."""
    node = load_model(app, spec.path)
    node.reparentTo(holder)
    node.setHpr(spec.heading, spec.pitch, 0)
    fit_to_height(node, holder, spec.height)
    make_lit(holder)
    return node
