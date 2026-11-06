from collections.abc import Iterator

import pytest


@pytest.fixture
def registered_viewer_scene_objects() -> Iterator[None]:
    """Register Viewer scene objects for one isolated test."""
    pytest.importorskip("compas_viewer")

    from compas.scene.context import ITEM_SCENEOBJECT
    from compas_model.plugins import register_scene_objects as register_model_scene_objects
    from compas_viewer.plugins import register_scene_objects as register_viewer_scene_objects

    context_existed = "Viewer" in ITEM_SCENEOBJECT
    previous = dict(ITEM_SCENEOBJECT.get("Viewer", {}))
    try:
        register_viewer_scene_objects()
        register_model_scene_objects()
        yield
    finally:
        if context_existed:
            ITEM_SCENEOBJECT["Viewer"].clear()
            ITEM_SCENEOBJECT["Viewer"].update(previous)
        else:
            ITEM_SCENEOBJECT.pop("Viewer", None)
