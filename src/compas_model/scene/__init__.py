from .elementobject import ElementObject
from .blockobject import BlockObject
from compas_model.elements import Block
from compas_model.elements import Element
from compas.plugins import plugin
from compas.scene import register


@plugin(category="factories")
def register_scene_objects():
    print(
        "____________________________SceneObjects registered for compas_model.______________________________________"
    )
    register(Element, ElementObject)
    register(Block, BlockObject)


@plugin(category="factories", pluggable_name="register_scene_objects")
def register_scene_objects_base():
    print(
        "____________________________SceneObjects registered for compas_model.______________________________________"
    )
    register(Element, ElementObject)
    register(Block, BlockObject)


__all__ = [
    "ElementObject",
    "BlockObject",
]
