"""Validate plugin discovery from an installed COMPAS Model wheel."""

import sys
from importlib.metadata import distribution
from importlib.util import find_spec

from compas.geometry import Box
from compas.plugins import ExtensionPoint
from compas.plugins import PluginManager
from compas.scene import Scene
from compas_model.elements import MeshElement
from compas_model.models import Model
from compas_model.scene import ElementObject
from compas_model.scene import ModelObject


entry_points = [entry_point for entry_point in distribution("compas_model").entry_points if entry_point.group == "compas.plugins"]
assert [(entry_point.name, entry_point.value) for entry_point in entry_points] == [("compas_model", "compas_model.plugins")]

manager = PluginManager(entry_points_provider=lambda *, group: entry_points)
assert manager.load_plugins() == 2

type_factory = ExtensionPoint(
    domain="https://plugins.compas.dev/",
    category="factories",
    name="register_scene_objects",
)
operation_factory = ExtensionPoint(
    domain="https://plugins.compas.dev/",
    category="factories",
    name="register_scene_operations",
)
assert [(implementation.id, implementation.spec.requires) for implementation in manager.registry[type_factory]] == [
    ("compas_model.plugins.register_scene_objects", ()),
]
assert [(implementation.id, implementation.spec.requires) for implementation in manager.registry[operation_factory]] == [
    ("compas_model.plugins.register_scene_operations", ("compas_viewer",)),
]

with_viewer = sys.argv[1:] == ["--viewer"]
assert (find_spec("compas_viewer") is not None) == with_viewer
assert manager.select(type_factory) is not None
assert bool(manager.collect(operation_factory)) == with_viewer
assert not [
    name
    for name in sys.modules
    if name == "compas_viewer"
    or name.startswith("compas_viewer.")
    or name == "PySide6"
    or name.startswith("PySide6.")
    or name == "OpenGL"
    or name.startswith("OpenGL.")
    or name == "compas_model.viewer"
    or name.startswith("compas_model.viewer.")
]

model = Model()
element = model.add_element(MeshElement(Box().to_polygonal_surface().to_mesh()))
scene = Scene()
root = scene.add(model)
child = scene.add(element, parent=root)
assert type(root) is ModelObject
assert type(child) is ElementObject
assert root.children == (child,)
assert not any(name.split(".")[0] in {"PySide6", "OpenGL"} for name in sys.modules)
assert "compas_model.viewer" not in sys.modules

if with_viewer:
    from compas_model.viewer.elementobject import ElementObject as ElementRenderer
    from compas_viewer.scene import ViewerScene

    view_scene = ViewerScene()
    view_root = view_scene.add(model)
    view_child = view_scene.add(element, parent=view_root)
    view_scene.prepare()
    renderer = view_scene.render_object(view_child)
    assert isinstance(renderer, ElementRenderer)
    assert renderer.sceneobject is view_child
    geometry = renderer.render_geometry
    assert geometry is not None
    view_scene.prepare()
    assert view_scene.render_object(view_child).render_geometry is geometry
    view_scene.clear_object(view_child)
    assert view_child.guid not in view_scene.render_objects
    assert view_scene.object(view_child.guid) is view_child
