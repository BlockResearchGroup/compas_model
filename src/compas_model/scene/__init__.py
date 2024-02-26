from compas.plugins import plugin
from compas.scene import register

from compas_model.elements import Element
from .elementobject import ElementObject


@plugin(category="factories")
def register_scene_objects():
    register(Element, ElementObject)


__all__ = [
    "ElementObject",
]
