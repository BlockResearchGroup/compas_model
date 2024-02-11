from compas.files import OBJ
from compas_model.elements import BlockElement
from compas_model.model import Model
from compas_model.algorithms import collider
from compas.datastructures import Mesh

# Read the OBJ file of Cross vault.
obj = OBJ('data/cross_vault.obj')
obj.read()

# Create elements from meshes and add them to the model.
model = Model()
for name in obj.objects:
    mesh = Mesh.from_vertices_and_faces(*obj.objects[name])
    block = BlockElement(mesh)
    block.frame = block.aabb.frame
    model.add_element(block)


# Get the collision pairs and add interactions to the model.
collision_pairs = collider.get_collision_pairs(model, 0.01, True, True, 0.1, 10)

# Extract the interface pollygons and add interactions.
interfaces = []
for pair in collision_pairs:
    model.add_interaction_by_index(pair[0], pair[1])
    for interface in pair[2]:
        interfaces.append(interface[1])
interfaces.extend(model.get_interactions_lines(True))
