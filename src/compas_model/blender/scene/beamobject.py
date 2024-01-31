from compas_blender.scene import BlenderSceneObject
from compas_model.scene import ElementObject


class BlenderBeamObject(BlenderSceneObject, ElementObject):
    def draw(self):
        """Draw the object representing the element."""
        pass
