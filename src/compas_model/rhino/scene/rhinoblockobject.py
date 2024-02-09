from compas_rhino.scene import RhinoSceneObject
from compas_model.scene import ElementObject

import scriptcontext as sc
from compas_rhino.conversions import mesh_to_rhino


class RhinoBlockObject(RhinoSceneObject, ElementObject):
    def __init__(self, element, **kwargs):
        super(RhinoBlockObject, self).__init__(element=element, **kwargs)

    def draw(self):
        """Draw the object representing the element."""
        # Development in progress.
        print(self.element.geometry)
        mesh = mesh_to_rhino(self.element.geometry)
        self._guid_mesh = sc.doc.Objects.AddMesh(mesh)
        self._guids = []
        self._guids.append(self._guid_mesh)
        return self._guids
