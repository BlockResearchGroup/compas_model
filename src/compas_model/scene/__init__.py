from .elementobject import ElementObject
from .blockobject import BlockObject
from compas_model.elements import BlockElement
from compas_model.elements import Element
from compas.plugins import plugin
from compas.scene import register


@plugin(category="factories")
def register_scene_objects():
    register(Element, ElementObject)
    register(BlockElement, BlockObject)


__all__ = [
    "ElementObject",
    "BlockObject",
]
