from compas.plugins import plugin
from compas.scene import register

from compas_model.elements import Element

from compas_model.models import Model

try:
    import compas_viewer  # noqa: F401

    from .elementobject import ElementObject
    from .modelobject import ModelObject

    @plugin(category="factories")
    def register_scene_objects():
        register(Element, ElementObject, context="Viewer")
        register(Model, ModelObject, context="Viewer")

    __all__ = [
        "ElementObject",
        "ModelObject",
    ]


except ImportError:
    pass
