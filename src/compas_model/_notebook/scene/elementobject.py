from compas_model.scene import ElementObject
from compas_notebook.scene import ThreeSceneObject


class ThreeElementObject(ThreeSceneObject, ElementObject):
    """Scene object for drawing mesh."""

    def __init__(self, element, **kwargs):
        super().__init__(element=element, **kwargs)
