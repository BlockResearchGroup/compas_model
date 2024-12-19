"""This package provides scene object plugins for visualising COMPAS Model objects in Rhino.
When working in Rhino, :class:`compas.scene.SceneObject` will automatically use
the corresponding Rhino scene object for each COMPAS model object type.

"""

from compas.plugins import plugin
from compas.scene import register

from compas_model.elements import BlockElement
from compas_model.models import Model

from .blockobject import ThreeBlockObject
from .modelobject import ThreeModelObject


@plugin(category="factories", requires=["pythreejs"])
def register_scene_objects():
    register(BlockElement, ThreeBlockObject, context="Notebook")
    register(Model, ThreeModelObject, context="Notebook")

    # print("PyThreeJS Model elements registered.")


__all__ = [
    "ThreeBlockObject",
    "ThreeModelObjec",
]
