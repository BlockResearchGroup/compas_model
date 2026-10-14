import sys
from dataclasses import is_dataclass
from typing import Any
from typing import cast
from typing import get_type_hints


def prepare_viewer_backend() -> None:
    """Apply compatibility fixes required by the installed COMPAS Viewer.

    Notes
    -----
    COMPAS Viewer 2.0.1 reads ``__annotations__`` directly from nested
    dataclass instances, which is incompatible with Python 3.14's deferred
    annotation representation. The patch can be removed when the upstream
    configuration loader supports Python 3.14.

    """
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
            elif isinstance(field_value, dict):
                raise ValueError(f"Expected dataclass type for field {field_name!r} but got a dictionary.")

    setattr(ConfigBase, "__post_init__", post_init)
    setattr(ConfigBase, "_compas_model_python314_compatible", True)
