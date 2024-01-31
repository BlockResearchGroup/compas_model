"""This package provides scene object plugins for visualising COMPAS objects in Jupyter Notebooks using three.
When working in a notebook, :class:`compas.scene.SceneObject` will automatically use the corresponding PyThreeJS scene object for each COMPAS object type.

"""
from compas.plugins import plugin
from compas.scene import register

from compas_model.elements import Beam
from .beamobject import BlenderBeamObject


@plugin(category="factories", requires=["bpy"])
def register_scene_objects():
    register(Beam, BlenderBeamObject, context="Blender")
    print("Blender SceneObjects registered for compas_model.")


__all__ = [
    "BlenderBeamObject",
]
