import numpy as np

import compas
from compas.colors import Color
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import oriented_bounding_box_numpy
from compas.geometry.bbox_numpy import minimum_volume_box
from compas_viewer import Viewer

mesh = Mesh.from_obj(compas.get("tubemesh.obj"))

faces = list(mesh.faces())

boxes = [Box.from_bounding_box(minimum_volume_box(np.asarray(mesh.face_points(face)))) for face in faces]

# =============================================================================
# Viz
# =============================================================================

viewer = Viewer()
viewer.scene.add(mesh)
viewer.scene.add(boxes[:10], show_faces=False)
viewer.show()
