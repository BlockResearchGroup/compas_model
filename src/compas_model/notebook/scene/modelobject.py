from compas_notebook.scene import ThreeSceneObject

from compas_model.scene import ElementObject
from compas_model.scene import ModelObject


class ThreeModelObject(ThreeSceneObject, ModelObject):
    """Scene object for drawing block objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def draw(self):
        """Draw the mesh associated with the scene object.

        Returns
        -------
        list
            List of pythreejs objects created.

        """
        for child in self.children:
            if isinstance(child, ElementObject):
                child.show = self.show_elements

        return self.guids
