import os
import subprocess
import sys
from importlib.metadata import EntryPoint
from pathlib import Path

import pytest
from compas.plugins import ExtensionPoint
from compas.plugins import PluginManager
from compas.scene.context import ITEM_SCENEOBJECT

import compas_model
from compas_model import plugins


FACTORY_EXTENSION = ExtensionPoint(
    domain="https://plugins.compas.dev/",
    category="factories",
    name="register_scene_objects",
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

    assert installed.load_plugins() == 1
    assert plugin_contract(installed) == plugin_contract(direct)
    assert plugin_contract(installed)[FACTORY_EXTENSION] == [
        ("compas_model.plugins.register_scene_objects", ("compas_viewer",)),
    ]


def test_viewer_factory_is_not_selected_without_its_runtime(monkeypatch):
    manager = PluginManager(entry_points_provider=lambda *, group: candidate_plugin_entry_points())
    assert manager.load_plugins() == 1
    monkeypatch.setattr(manager, "verify_requirement", lambda requirement: False)

    assert manager.select(FACTORY_EXTENSION) is None


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
assert manager.load_plugins() == 1
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
    environment["PYTHONPATH"] = str(SOURCE)

    subprocess.run([sys.executable, "-c", script], env=environment, check=True, capture_output=True, text=True)


def test_register_scene_objects_uses_viewer_context_and_preserves_import_errors(monkeypatch):
    pytest.importorskip("compas_viewer")
    from compas_model.elements import Element
    from compas_model.models import Model
    from compas_model.viewer import ElementObject
    from compas_model.viewer import ModelObject

    previous = dict(ITEM_SCENEOBJECT["Viewer"])
    try:
        ITEM_SCENEOBJECT["Viewer"].clear()
        plugins.register_scene_objects()

        registry = ITEM_SCENEOBJECT["Viewer"]
        assert registry[Element] is ElementObject
        assert registry[Model] is ModelObject

        monkeypatch.setitem(sys.modules, "compas_model.viewer.elementobject", None)
        with pytest.raises(ModuleNotFoundError):
            plugins.register_scene_objects()
    finally:
        ITEM_SCENEOBJECT["Viewer"].clear()
        ITEM_SCENEOBJECT["Viewer"].update(previous)
