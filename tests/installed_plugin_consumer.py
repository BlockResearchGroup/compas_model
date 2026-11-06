"""Validate plugin discovery from an installed COMPAS Model wheel."""

import sys
from importlib.metadata import distribution
from importlib.util import find_spec

from compas.plugins import ExtensionPoint
from compas.plugins import PluginManager


entry_points = [entry_point for entry_point in distribution("compas_model").entry_points if entry_point.group == "compas.plugins"]
assert [(entry_point.name, entry_point.value) for entry_point in entry_points] == [("compas_model", "compas_model.plugins")]

manager = PluginManager(entry_points_provider=lambda *, group: entry_points)
assert manager.load_plugins() == 1

extension_point = ExtensionPoint(
    domain="https://plugins.compas.dev/",
    category="factories",
    name="register_scene_objects",
)
implementations = manager.registry[extension_point]
assert [(implementation.id, implementation.spec.requires) for implementation in implementations] == [
    ("compas_model.plugins.register_scene_objects", ("compas_viewer",)),
]

assert find_spec("compas_viewer") is None
assert manager.select(extension_point) is None
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
