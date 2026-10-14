# ruff: noqa: F401

from compas.plugins import plugin
from compas.scene import register

from compas_model.elements import Element
from compas_model.models import Model

from .rendergeometry import RenderGeometry
from .rendergeometry import RenderRepresentation
from .rendergeometry import render_geometry_from_brep
from .rendergeometry import render_geometry_from_mesh
from .viewstate import RenderGeometryCache
from .viewstate import RenderQuality
from .viewstate import RenderSettings

try:
    import compas_viewer  # noqa: F401

    from .compat import prepare_viewer_backend
    from .contactlayer import ContactKey
    from .contactlayer import ContactLayer
    from .contactlayer import ContactView
    from .controller import ModelViewer
    from .elementobject import ElementObject
    from .inspector import ElementInspector
    from .inspector import InspectorSection
    from .inspector import inspect_elements
    from .inspector import install_element_inspector
    from .interactionform import ContactSelection
    from .interactionform import InteractionSelection
    from .interactionform import InteractionTreeForm
    from .modelobject import ModelObject
    from .navigation import ModelNavigationForm
    from .navigation import install_model_navigation
    from .treeform import ModelTreeForm
    from .treeform import install_model_tree

    @plugin(category="factories")
    def register_scene_objects() -> None:
        register(Element, ElementObject, context="Viewer")
        register(Model, ModelObject, context="Viewer")


except ImportError:
    pass
