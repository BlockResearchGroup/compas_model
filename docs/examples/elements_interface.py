from compas.geometry import Polygon, Frame, Box
from compas.datastructures import Mesh
from compas_model.elements import Interface, Block
from compas_model.model import Model


# --------------------------------------------------------------------------
# Create model.
# --------------------------------------------------------------------------
model = Model()

# --------------------------------------------------------------------------
# Create plate from two polygons.
# --------------------------------------------------------------------------
mesh = Mesh.from_polyhedron(4)
box0 = Mesh.from_vertices_and_faces(*(Box(2, 2, 2, Frame([-1.5, 0, 0], [1, 0, 0], [0, 1, 0])).to_vertices_and_faces()))
box1 = Mesh.from_vertices_and_faces(*(Box(2, 2, 2, Frame([1.5, 0, 0], [1, 0, 0], [0, 1, 0])).to_vertices_and_faces()))
polygon = Polygon([[0, -1, -1], [0, 1, -1], [0, 1, 1], [0, -1, 1]])
block0 = Block(box0)
block1 = Block(box1)
interface = Interface(polygon)
interface_copy = interface.copy()

# --------------------------------------------------------------------------
# Or test the example file.
# --------------------------------------------------------------------------
model.add_elements([block0, block1, interface])
model.add_interaction(block0, interface)
model.add_interaction(block1, interface)
model.print()
print("Beam block0 belongs to the following ElementNode: ",  block0.node)
print("Beam block1 belongs to the following ElementNode: ",  block1.node)
print("Beam interface belongs to the following ElementNode: ",  interface.node)