import compas_model.model
from compas_notebook.scene import ThreeSceneObject


class ThreeModelObject(ThreeSceneObject):
    def __init__(self, model: compas_model.model.Model, **kwargs):
        super().__init__(item=model, **kwargs)
        self.model = model
        self.show_hierarchy = False
        self.show_interactions = False
        self.show_elements = True

    def draw(self):
        if self.show_elements:
            for element in self.model.elementlist:
                pass
