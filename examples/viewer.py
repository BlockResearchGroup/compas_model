"""Shared COMPAS Model viewer utilities for executable visual examples."""

from compas.colors import Color
from compas.datastructures import Mesh
from compas.geometry import Brep
from compas_model.elements import BrepElement
from compas_model.elements import MeshElement
from compas_model.models import Model
from compas_model.viewer import ModelViewer

BLUE = Color(0.20, 0.45, 0.85)
GREEN = Color(0.20, 0.70, 0.35)
AMBER = Color(0.95, 0.60, 0.10)
RED = Color(0.85, 0.20, 0.20)
GREY = Color(0.55, 0.58, 0.62)
DARK = Color(0.12, 0.14, 0.18)


def validate_viewer_backend():
    """Validate the viewer dependency without opening a window."""

    from compas_viewer.config import Config

    Config()


def show_scene(title, objects, labels):
    """Display example geometry through the COMPAS Model viewer."""
    from compas_viewer.scene import Tag

    model = Model()
    elements = []

    for geometry, name, color, opacity in objects:
        if isinstance(geometry, Mesh):
            element = MeshElement(geometry=geometry, name=name)
        elif isinstance(geometry, Brep):
            element = BrepElement(geometry=geometry, name=name)
        else:
            raise TypeError(f"Unsupported example geometry: {type(geometry).__name__}.")
        model.add_element(element)
        elements.append((element, color, opacity))

    controller = ModelViewer(model)
    controller.viewer.config.window.title = title

    for element, color, opacity in elements:
        scene_object = controller.object_for_element(element)
        scene_object.facecolor = color
        scene_object.edgecolor = DARK
        scene_object.opacity = opacity

    for text, position, color in labels:
        controller.viewer.scene.add(Tag(text, position, color=color, height=18))

    controller.show_viewer()
