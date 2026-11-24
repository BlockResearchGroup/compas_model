import pytest


@pytest.fixture
def registered_viewer_scene_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register Viewer scene objects for one isolated test."""
    pytest.importorskip("compas_viewer")

    from compas.scene import context
    from compas_model.plugins import ensure_scene_objects_registered
    from compas_viewer.plugins import register_scene_operations

    operations = {key: {cls: dict(ops) for cls, ops in types.items()} for key, types in context.SCENE_OPERATIONS.items()}
    monkeypatch.setattr(context, "SCENEOBJECT_TYPES", dict(context.SCENEOBJECT_TYPES))
    monkeypatch.setattr(context, "SCENE_OPERATIONS", operations)
    monkeypatch.setattr(context, "_SCENEOBJECTS_DISCOVERED", context._SCENEOBJECTS_DISCOVERED)
    monkeypatch.setattr(context, "_OPERATIONS_DISCOVERED", context._OPERATIONS_DISCOVERED)
    ensure_scene_objects_registered()
    register_scene_operations()
