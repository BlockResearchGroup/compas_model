"""COMPAS plugin implementations provided by :mod:`compas_model`."""

from importlib.util import find_spec
from typing import TYPE_CHECKING

from compas.plugins import plugin

if TYPE_CHECKING:
    from compas.scene import Scene
    from compas_model.scene import ElementObject


@plugin(category="factories")
def register_scene_objects() -> None:
    """Register stable scene-object types for models and elements."""
    from compas.scene import register_sceneobject_type
    from compas_model.elements import Element
    from compas_model.models import Model
    from compas_model.scene import ElementObject
    from compas_model.scene import ModelObject

    register_sceneobject_type(Element, ElementObject)
    register_sceneobject_type(Model, ModelObject)


@plugin(category="factories", requires=["compas_viewer"])
def register_scene_operations() -> None:
    """Register Viewer operations for element scene objects."""
    from compas.scene import register_scene_operation
    from compas_model.scene import ElementObject

    register_scene_operation("Viewer", ElementObject, "draw", _draw_element)
    register_scene_operation("Viewer", ElementObject, "clear", _clear_element)


def _draw_element(scene: "Scene", target: "ElementObject", runtime: object | None) -> list[object]:
    from compas_model.viewer.elementobject import draw_element

    return draw_element(scene, target, runtime)


def _clear_element(scene: "Scene", target: "ElementObject", runtime: object | None, resources: tuple[object, ...]) -> None:
    from compas_viewer.scene.runtime import clear

    clear(scene, target, runtime, resources)


def ensure_scene_objects_registered() -> None:
    """Register Model scene support directly for source checkouts."""
    register_scene_objects()
    if find_spec("compas_viewer") is not None:
        register_scene_operations()


__all__ = ["ensure_scene_objects_registered", "register_scene_objects", "register_scene_operations"]
