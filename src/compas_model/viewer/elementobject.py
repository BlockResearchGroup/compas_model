from typing import Any
from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas_model.elements import Group
from compas_model.scene.elementobject import ElementObject as BaseElementObject
from compas_viewer.scene import MeshObject
from compas_viewer.scene import ViewerSceneObject
from compas_viewer.scene.brepobject import BRepObject
from compas_viewer.scene.sceneobject import ShaderDataType


class ElementObject(ViewerSceneObject, BaseElementObject):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        if isinstance(self.element, Group):
            self.visualization_object = None
            return

        geometry = self.element.modelgeometry
        if isinstance(geometry, Mesh):
            mesh_kwargs = kwargs.copy()
            mesh_kwargs["item"] = geometry
            self.visualization_object = MeshObject(**mesh_kwargs)
        elif isinstance(geometry, Brep):
            brep_kwargs = kwargs.copy()
            brep_kwargs["item"] = geometry
            self.visualization_object = BRepObject(**brep_kwargs)
        else:
            self.visualization_object = None

    def _read_points_data(self) -> Optional[ShaderDataType]:
        if self.visualization_object:
            return self.visualization_object._read_points_data()

    def _read_lines_data(self) -> Optional[ShaderDataType]:
        if self.visualization_object:
            return self.visualization_object._read_lines_data()

    def _read_frontfaces_data(self) -> Optional[ShaderDataType]:
        if self.visualization_object:
            return self.visualization_object._read_frontfaces_data()

    def _read_backfaces_data(self) -> Optional[ShaderDataType]:
        if self.visualization_object:
            return self.visualization_object._read_backfaces_data()
