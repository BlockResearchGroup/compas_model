from compas_rhino.scene import RhinoSceneObject
from compas_model.scene import ElementObject


class RhinoBeamObject(RhinoSceneObject, ElementObject):
    def draw(self):
        """Draw the object representing the element."""
        pass
