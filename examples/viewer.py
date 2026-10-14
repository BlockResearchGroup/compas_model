"""Shared COMPAS Viewer utilities for executable visual examples."""

import sys
from dataclasses import is_dataclass
from typing import Any
from typing import cast
from typing import get_type_hints

from compas.colors import Color

BLUE = Color(0.20, 0.45, 0.85)
GREEN = Color(0.20, 0.70, 0.35)
AMBER = Color(0.95, 0.60, 0.10)
RED = Color(0.85, 0.20, 0.20)
GREY = Color(0.55, 0.58, 0.62)
DARK = Color(0.12, 0.14, 0.18)


def prepare_viewer_backend():
    """Apply the COMPAS Viewer 2.0.1 compatibility fix for Python 3.14."""
    if sys.version_info < (3, 14):
        return

    from compas_viewer.config import ConfigBase

    if getattr(ConfigBase, "_compas_model_python314_compatible", False):
        return

    def post_init(self: Any) -> None:
        annotations = get_type_hints(type(self))
        for field_name, field_value in self.__dict__.items():
            field_type = cast(Any, annotations[field_name])
            if isinstance(field_value, dict) and is_dataclass(field_type):
                setattr(self, field_name, cast(Any, field_type)(**field_value))
            elif isinstance(field_value, dict) and not is_dataclass(field_type):
                raise ValueError(f"Expected dataclass type for field '{field_name}' but got dict.")

    setattr(ConfigBase, "__post_init__", post_init)
    setattr(ConfigBase, "_compas_model_python314_compatible", True)


def validate_viewer_backend():
    """Construct the viewer configuration without opening a window."""
    prepare_viewer_backend()

    from compas_viewer.config import Config

    Config()


def show_scene(title, objects, labels):
    """Display example geometry and labels in COMPAS Viewer."""
    prepare_viewer_backend()

    from compas_viewer import Viewer
    from compas_viewer.scene import Tag

    viewer = Viewer()
    viewer.config.window.title = title

    for geometry, name, color, opacity in objects:
        viewer.scene.add(
            geometry,
            name=name,
            facecolor=color,
            linecolor=DARK,
            opacity=opacity,
            show_lines=True,
        )

    for text, position, color in labels:
        viewer.scene.add(Tag(text, position, color=color, height=18, absolute_height=True))

    viewer.show()
