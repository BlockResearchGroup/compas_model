"""COMPAS plugin implementations provided by :mod:`compas_model`."""

import sys

from compas.plugins import plugin
from compas.scene import register


@plugin(category="factories", requires=["compas_viewer"])
def register_scene_objects() -> None:
    """Register COMPAS Model scene objects for COMPAS Viewer."""
    from compas_model.elements import Element
    from compas_model.models import Model
    from compas_model.viewer.elementobject import ElementObject
    from compas_model.viewer.modelobject import ModelObject

    register(Element, ElementObject, context="Viewer")
    register(Model, ModelObject, context="Viewer")


def ensure_scene_objects_registered() -> None:
    """Ensure COMPAS Model's Viewer scene objects are registered.

    The plugin entry point handles normal installed-package discovery. This
    explicit hook also supports editable source checkouts and processes in
    which another package populated the scene-object registry first.

    """
    from compas.plugins import plugin_manager
    from compas.scene import register_scene_objects as register_all_scene_objects
    from compas.scene.context import ITEM_SCENEOBJECT
    from compas_model.elements import Element
    from compas_model.models import Model
    from compas_model.viewer.elementobject import ElementObject
    from compas_model.viewer.modelobject import ModelObject

    expected = {
        Element: ElementObject,
        Model: ModelObject,
    }
    registry = ITEM_SCENEOBJECT.get("Viewer", {})
    if all(registry.get(item_type) is sceneobject_type for item_type, sceneobject_type in expected.items()):
        return

    plugin_manager.register_module(sys.modules[__name__])
    register_all_scene_objects()


__all__ = ["ensure_scene_objects_registered", "register_scene_objects"]
