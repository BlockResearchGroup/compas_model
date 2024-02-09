"""This package provides scene object plugins for visualising COMPAS objects in Jupyter Notebooks using three.
When working in a notebook, :class:`compas.scene.SceneObject` will automatically use the corresponding PyThreeJS scene object for each COMPAS object type.

"""
from compas.plugins import plugin
from compas.scene import register

from compas_model.elements import Block
from .beamobject import BlenderBlockObject


@plugin(category="factories", requires=["bpy"])
def register_scene_objects():
    register(Block, BlenderBlockObject, context="Blender")


__all__ = [
    "BlenderBeamObject",
]
