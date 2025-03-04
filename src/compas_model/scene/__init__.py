from compas.plugins import plugin
from compas.scene import register

from compas_model.elements import Element

from compas_model.models import Model
from .elementobject import ElementObject
from .modelobject import ModelObject
from .viewerelementobject import ViewerElementObject
from .viewermodelobject import ViewerModelObject


@plugin(category="factories")
def register_scene_objects():
    register(Element, ElementObject)
    register(Model, ModelObject)
    register(Element, ViewerElementObject, context="Viewer")
    register(Model, ViewerModelObject, context="Viewer")

__all__ = [
    "ElementObject",
    "ModelObject",
    "ViewerModelObject",
]
