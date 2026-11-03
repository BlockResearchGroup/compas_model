from compas.scene.context import ITEM_SCENEOBJECT

from compas_model.elements import Element
from compas_model.models import Model
from compas_model.plugins import ensure_scene_objects_registered
from compas_model.viewer import ElementObject
from compas_model.viewer import ModelObject


def test_ensure_scene_objects_registered():
    ensure_scene_objects_registered()

    registry = ITEM_SCENEOBJECT["Viewer"]
    assert registry[Element] is ElementObject
    assert registry[Model] is ModelObject
