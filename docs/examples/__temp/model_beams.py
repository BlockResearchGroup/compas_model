from compas.datastructures import Mesh
from compas.files import OBJ
from compas_model.algorithms import collisions
from compas_model.elements import BlockElement
from compas_model.models import Model

obj = OBJ("data/beams3.obj")
obj.read()
meshes = []
for name in obj.objects:
    mesh = Mesh.from_vertices_and_faces(*obj.objects[name])
    mesh.name = name
    meshes.append(mesh)

# # Create elements from meshes and add them to the model.
model = Model()
elements = []
for mesh in meshes:
    block = BlockElement(mesh)
    elements.append(block)
    model.add_element(block)


# Get the collision pairs and add interactions to the model.
collision_pairs = collisions.get_collision_pairs(model, 0.01, True, True, 1, 0.001)

# Extract the interface pollygons and add interactions.
interfaces = []
for pair in collision_pairs:
    model.add_interaction(elements[pair[0]], elements[pair[1]])
    for interface in pair[2]:
        interfaces.append(interface[1])
        print(interface[0])
