from compas.files import OBJ
from compas.datastructures import Mesh
from compas_model.viewer import ViewerModel
from compas_model.elements import Block
from compas_model.model import Model
from compas_model.algorithms import Collider
from compas.geometry import Point

obj = OBJ('data/robot_kuka.obj')
obj.read()
meshes = []
for name in obj.objects:
    mesh = Mesh.from_vertices_and_faces(* obj.objects[name])
    mesh.name = name
    meshes.append(mesh)

# from compas.files import STL
# 

# 
# from compas.datastructures import Mesh

# meshes = Mesh.from_stl('data/beams3.stl').exploded()

# # Create elements from meshes and add them to the model.
model = Model()
elements = []
for mesh in meshes:
    block = Block(closed_mesh=mesh, geometry_simplified=Point(0, 0, 0))
    elements.append(block)
    model.add_element("my_block", block)


# Get the collision pairs and add interactions to the model.
# collision_pairs = Collider.get_collision_pairs(model, 0.01, True, True, 1, 0.001)

# # Extract the interface pollygons and add interactions.
# interfaces = []
# for pair in collision_pairs:
#     print(pair[0], pair[1])
#     model.add_interaction(elements[pair[0]], elements[pair[1]])
#     for interface in pair[2]:
#         interfaces.append(interface[1])
# interfaces.extend(model.get_interactions_lines())

# for element in elements:
#     print(element.collision_mesh)

# model.print()
# Show the model in the viewer.
ViewerModel.show(model, scale_factor=0.01, geometry=meshes)
