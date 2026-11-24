import os
import subprocess
import sys
from importlib.metadata import EntryPoint
from pathlib import Path

from compas.plugins import ExtensionPoint
from compas.plugins import PluginManager

import compas_model
from compas_model import plugins


FACTORY_EXTENSION = ExtensionPoint(
    domain="https://plugins.compas.dev/",
    category="factories",
    name="register_scene_objects",
)
OPERATIONS_EXTENSION = ExtensionPoint(
    domain="https://plugins.compas.dev/",
    category="factories",
    name="register_scene_operations",
)
SOURCE = Path(__file__).parents[1] / "src"


def candidate_plugin_entry_points() -> list[EntryPoint]:
    return [EntryPoint(name="compas_model", value="compas_model.plugins", group="compas.plugins")]


def plugin_contract(manager: PluginManager):
    return {
        extension_point: [(implementation.id, implementation.spec.requires) for implementation in implementations] for extension_point, implementations in manager.registry.items()
    }


def test_legacy_plugin_module_list_is_removed():
    assert not hasattr(compas_model, "__all_plugins__")


def test_candidate_entry_point_matches_direct_plugin_registration():
    entry_points = candidate_plugin_entry_points()
    assert [(entry_point.name, entry_point.value) for entry_point in entry_points] == [("compas_model", "compas_model.plugins")]

    installed = PluginManager(entry_points_provider=lambda *, group: entry_points)
    direct = PluginManager(entry_points_provider=lambda *, group: ())
    direct.register_module(plugins)

    assert installed.load_plugins() == 2
    assert plugin_contract(installed) == plugin_contract(direct)
    assert plugin_contract(installed)[FACTORY_EXTENSION] == [
        ("compas_model.plugins.register_scene_objects", ()),
    ]
    assert plugin_contract(installed)[OPERATIONS_EXTENSION] == [
        ("compas_model.plugins.register_scene_operations", ("compas_viewer",)),
    ]


def test_viewer_factory_is_not_selected_without_its_runtime(monkeypatch):
    manager = PluginManager(entry_points_provider=lambda *, group: candidate_plugin_entry_points())
    assert manager.load_plugins() == 2
    monkeypatch.setattr(manager, "verify_requirement", lambda requirement: False)

    assert manager.select(FACTORY_EXTENSION) is not None
    assert manager.collect(OPERATIONS_EXTENSION) == []


def test_entry_point_discovery_is_viewer_runtime_free():
    script = """
import sys
from importlib.metadata import EntryPoint
from compas.plugins import PluginManager

entry_points = [
    EntryPoint(
        name="compas_model",
        value="compas_model.plugins",
        group="compas.plugins",
    )
]
manager = PluginManager(entry_points_provider=lambda *, group: entry_points)
assert manager.load_plugins() == 2
unexpected = sorted(
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
)
assert not unexpected, unexpected
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, (str(SOURCE), environment.get("PYTHONPATH"))))

    subprocess.run([sys.executable, "-c", script], env=environment, check=True, capture_output=True, text=True)


def test_model_scene_roundtrip_restores_stable_types_and_hierarchy(monkeypatch):
    from compas.data import json_dumps
    from compas.data import json_loads
    from compas.scene import Scene
    from compas.scene import context
    from compas_model.elements import Group
    from compas_model.models import Model
    from compas_model.scene import ElementObject
    from compas_model.scene import ModelObject

    monkeypatch.setattr(context, "SCENEOBJECT_TYPES", dict(context.SCENEOBJECT_TYPES))
    monkeypatch.setattr(context, "_SCENEOBJECTS_DISCOVERED", context._SCENEOBJECTS_DISCOVERED)
    plugins.register_scene_objects()
    model = Model()
    element = model.add_element(Group(name="Assembly"))
    scene = Scene()
    root = scene.add(model)
    child = scene.add(element, parent=root)

    restored = json_loads(json_dumps(scene))
    restored.bind_many([model, element])
    restored_root = restored.object(root.guid)
    restored_child = restored.object(child.guid)

    assert type(restored_root) is ModelObject
    assert type(restored_child) is ElementObject
    assert restored_root.item is model
    assert restored_child.item is element
    assert restored_root.children == (restored_child,)
