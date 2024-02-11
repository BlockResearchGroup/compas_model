from compas_rhino.scene import RhinoSceneObject
from compas_model.scene import ElementObject

import scriptcontext as sc
from compas_rhino.conversions import mesh_to_rhino
from compas_rhino.conversions import transformation_to_rhino


class RhinoBlockObject(RhinoSceneObject, ElementObject):
    def __init__(self, element, **kwargs):
        super(RhinoBlockObject, self).__init__(element=element, **kwargs)

    def draw(self):
        """Draw the block object or its components in Rhino.

        Returns
        -------
        list[System.Guid]
            The GUIDs of the created Rhino objects.

        """

        self._guids = []

        # Blocks are meshes
        attr = self.compile_attributes(name=self.element.name)
        rhino_mesh = mesh_to_rhino(self.element.geometry)
        rhino_mesh.Transform(transformation_to_rhino(self.worldtransformation))
        self._guid_mesh = sc.doc.Objects.AddMesh(rhino_mesh, attr)

        # Collect the GUIDs
        self._guids.append(self._guid_mesh)
        return self._guids
