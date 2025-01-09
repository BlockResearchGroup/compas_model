from compas.datastructures import Mesh
from compas_model.elements import BlockElement
from compas_viewer import Viewer

mesh = Mesh.from_polyhedron(6)
block = BlockElement(mesh)


viewer = Viewer()
viewer.scene.add(block.compute_elementgeometry())
viewer.show()
