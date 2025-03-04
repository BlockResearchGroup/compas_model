from .modelobject import ModelObject
from compas_viewer.scene import ViewerSceneObject


class ViewerModelObject(ViewerSceneObject, ModelObject):

    def _read_points_data(self) -> None:
        pass

    def _read_lines_data(self) -> None:
        pass

    def _read_frontfaces_data(self) -> None:
        pass

    def _read_backfaces_data(self) -> None:
        pass

    
