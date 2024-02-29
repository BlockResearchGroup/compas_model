from compas_notebook.scene import ThreeSceneObject

from compas_model.scene import ElementObject


class ThreeElementObject(ThreeSceneObject, ElementObject):
    """Scene object for drawing mesh."""

    def __init__(self, element, **kwargs):
        super().__init__(element=element, **kwargs)
