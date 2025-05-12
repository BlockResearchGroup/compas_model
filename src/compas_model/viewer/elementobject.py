from compas.datastructures import Mesh
from compas.geometry import Brep
from compas_model.elements import Group
from compas_model.scene.elementobject import ElementObject as BaseElementObject
from compas_viewer.scene import MeshObject
from compas_viewer.scene import ViewerSceneObject


class ElementObject(ViewerSceneObject, BaseElementObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if isinstance(self.element, Group):
            self.visualization_object = None
        elif isinstance(self.element.modelgeometry, Mesh):
            mesh_kwargs = kwargs.copy()
            mesh_kwargs["item"] = self.element.modelgeometry
            self.visualization_object = MeshObject(**mesh_kwargs)
        elif isinstance(self.element.modelgeometry, Brep):
            # TODO: implement BRep visualization
            raise NotImplementedError("BRep is not supported yet.")
        else:
            self.visualization_object = None

    def _read_points_data(self):
        if self.visualization_object:
            return self.visualization_object._read_points_data()

    def _read_lines_data(self):
        if self.visualization_object:
            return self.visualization_object._read_lines_data()

    def _read_frontfaces_data(self):
        if self.visualization_object:
            return self.visualization_object._read_frontfaces_data()

    def _read_backfaces_data(self):
        if self.visualization_object:
            return self.visualization_object._read_backfaces_data()
