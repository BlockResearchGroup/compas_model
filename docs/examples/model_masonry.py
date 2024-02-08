from compas.files import OBJ
from compas_model.viewer import ViewerModel
from compas_model.elements import Block
from compas_model.model import Model
from compas_model.algorithms import Collider
from compas.datastructures import Mesh

# Read the OBJ file of Cross vault.
obj = OBJ('data/cross_vault.obj')
obj.read()

# Create elements from meshes and add them to the model.
model = Model()
elements = []
for name in obj.objects:
    mesh = Mesh.from_vertices_and_faces(*obj.objects[name])
    block = Block(closed_mesh=mesh)
    elements.append(block)
    model.add_element("my_block", block)


# Get the collision pairs and add interactions to the model.
collision_pairs = Collider.get_collision_pairs(model, 0.01, True, True, 0.1, 10)

# Extract the interface pollygons and add interactions.
interfaces = []
for pair in collision_pairs:
    model.add_interaction(elements[pair[0]], elements[pair[1]])
    for interface in pair[2]:
        interfaces.append(interface[1])
interfaces.extend(model.get_interactions_lines())

# Show the model in the viewer.
ViewerModel.show(model, scale_factor=0.025, geometry=interfaces)
