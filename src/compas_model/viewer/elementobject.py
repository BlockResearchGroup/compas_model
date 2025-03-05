from compas.colors import Color
from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Point
from compas_model.elements import GroupElement
from compas_model.scene.elementobject import ElementObject as BaseElementObject
from compas_viewer.scene import MeshObject
from compas_viewer.scene import ViewerSceneObject


class ElementObject(ViewerSceneObject, BaseElementObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if isinstance(self.modelgeometry, Mesh):
            mesh_kwargs = kwargs.copy()
            mesh_kwargs["item"] = self.modelgeometry
            self.visualization_object = MeshObject(**mesh_kwargs)
        elif isinstance(self.modelgeometry, Brep):
            # TODO: implement BRep visualization
            raise NotImplementedError("BRep is not supported yet.")
        else:
            self.visualization_object = None

    @property
    def modelgeometry(self) -> Mesh | Brep | None:
        if isinstance(self.element, GroupElement):
            return None
        else:
            return self.element.modelgeometry

    def _read_points_data(self) -> tuple[list[Point], list[Color], list[list[int]]] | None:
        if self.visualization_object:
            return self.visualization_object._read_points_data()

    def _read_lines_data(self) -> tuple[list[tuple[int, int]], list[Color], list[float]] | None:
        if self.visualization_object:
            return self.visualization_object._read_lines_data()

    def _read_frontfaces_data(self) -> tuple[list[list[int]], list[Color], list[float]] | None:
        if self.visualization_object:
            return self.visualization_object._read_frontfaces_data()

    def _read_backfaces_data(self) -> tuple[list[list[int]], list[Color], list[float]] | None:
        if self.visualization_object:
            return self.visualization_object._read_backfaces_data()
