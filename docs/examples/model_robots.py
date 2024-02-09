from compas.files import OBJ
from compas.datastructures import Mesh
from compas_model.elements import Block
from compas_model.model import Model
from compas.geometry import Point, Frame

# meshes
paths = [
    'data/robot_kuka_base.obj',
    'data/robot_kuka_axis0.obj',
    'data/robot_kuka_axis1.obj',
    'data/robot_kuka_axis2.obj',
    'data/robot_kuka_axis3.obj',
    'data/robot_kuka_axis4.obj',
    'data/robot_kuka_axis5.obj',
]
meshes = []

for path in paths:
    obj = OBJ(path)
    obj.read()
    for name in obj.objects:
        mesh = Mesh.from_vertices_and_faces(* obj.objects[name])
        mesh.name = name
        meshes.append(mesh)

# frames
origins = [[0, 0, 217], [24.512667, -6.66177, 400], [24.904867, -2.178893, 855], [145.743477, -12.750905, 869.151417], [443.020905, -38.51023, 816.506682], [519.30574, -44.271409, 816.486246]]
x_axes = [[1, 0, 0], [1, 0, 0], [1, 0, 0], [0, -1, 0], [1, 0, 0], [0, 0, -1]]
y_axes = [[0, 0, 1], [0, 1, 0], [0, 1, 0], [1, -0, 0], [0, 1, 0], [1, 0, 0]]
frames = []
for i in range(len(origins)):
    frames.append(Frame(origins[i], x_axes[i], y_axes[i]))

# Create elements from meshes and add them to the model.
model = Model()
model.add_element("robot_base", Block(closed_mesh=meshes[0], geometry_simplified=Point(0, 0, 0), frame=Frame.worldXY()))
for i in range(1, len(meshes)):
    block = Block(closed_mesh=meshes[i], geometry_simplified=Point(0, 0, 0), frame=frames[i-1])
    model.add_element("axis_"+str(i-1), block)

for i in range(1, len(meshes)-1):
    model.add_interaction(i, i+1)

# Display geometry
geometry = model.get_interactions_lines()
for element in model.elements_list:
    geometry.append(element.frame)

model.print()