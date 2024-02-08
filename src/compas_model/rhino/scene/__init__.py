"""This package provides scene object plugins for visualising COMPAS objects in Jupyter Notebooks using three.
When working in a notebook, :class:`compas.scene.SceneObject` will automatically use the corresponding PyThreeJS scene object for each COMPAS object type.

"""
from compas.plugins import plugin
from compas.scene import register

from compas_model.elements import Block
from .rhinoblockobject import RhinoBlockObject


@plugin(category="factories", requires=["Rhino"])
def register_scene_objects():
    register(Block, RhinoBlockObject, context="Rhino")
    print("Rhino SceneObjects registered for compas_model.")


__all__ = [
    "RhinoBlockObject",
]

# """This package provides scene object plugins for visualising COMPAS objects in Jupyter Notebooks using three.
# When working in a notebook, :class:`compas.scene.SceneObject` will automatically use the corresponding PyThreeJS scene object for each COMPAS object type.

# """
# from compas.plugins import plugin
# from compas.scene import register

# from compas_model.elements import Block
# from .blockobject import RhinoBlockObject


# @plugin(category="factories", requires=["Rhino"])
# def register_scene_objects():
#     register(Block, RhinoBlockObject, context="Rhino")
#     print("____________________________Rhino SceneObjects registered for compas_model.______________________________________")


# __all__ = [
#     "RhinoBlockObject",
# ]
