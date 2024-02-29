import scriptcontext as sc  # type: ignore
from compas_rhino.conversions import mesh_to_rhino
from compas_rhino.conversions import transformation_to_rhino
from compas_rhino.scene import RhinoSceneObject

from compas_model.scene import ElementObject


class RhinoBlockObject(RhinoSceneObject, ElementObject):
    def __init__(self, element, **kwargs):
        super(RhinoBlockObject, self).__init__(element=element, **kwargs)

    def draw(self):
        self._guids = []
        attr = self.compile_attributes(name=self.element.name)
        geometry = mesh_to_rhino(self.element.geometry)
        geometry.Transform(transformation_to_rhino(self.worldtransformation))
        guid = sc.doc.Objects.AddMesh(geometry, attr)
        self._guids.append(guid)
        return self._guids
