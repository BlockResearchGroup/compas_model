from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Polygon
from compas_model.elements import BlockElement
from compas_model.elements import InterfaceElement
from compas_model.models import Model

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
block0 = BlockElement(box0)
block1 = BlockElement(box1)
interface = InterfaceElement(polygon)
interface_copy = interface.copy()

# --------------------------------------------------------------------------
# Or test the example file.
# --------------------------------------------------------------------------
model.add_elements([block0, block1, interface])

for node in model.graph.nodes():
    print(node)

model.add_interaction(block0, interface)
model.add_interaction(block1, interface)
model.print()

model.add_interaction_by_index(0, 1)

print(block0.graph_node, block0.tree_node)
print(block1.graph_node, block1.tree_node)
print(interface.graph_node, interface.tree_node)
