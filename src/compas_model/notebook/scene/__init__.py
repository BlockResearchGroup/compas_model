from compas.plugins import plugin
from compas.scene import register

from compas_model.models import Model

from .elementobject import ThreeElementObject
from .modelobject import ThreeModelObject


@plugin(category="factories", requires=["pythreejs"])
def register_scene_objects():
    register(Model, ThreeModelObject, context="Notebook")


__all__ = [
    "ThreeElementObject",
    "ThreeModelObject",
]
