from compas.datastructures import Mesh
from compas.files import OBJ
from compas.geometry import Frame
from compas_model.elements import BlockElement
from compas_model.models import Model

# meshes
paths = [
    "data/robot_kuka_base.obj",
    "data/robot_kuka_axis0.obj",
    "data/robot_kuka_axis1.obj",
    "data/robot_kuka_axis2.obj",
    "data/robot_kuka_axis3.obj",
    "data/robot_kuka_axis4.obj",
    "data/robot_kuka_axis5.obj",
]
meshes = []

for path in paths:
    obj = OBJ(path)
    obj.read()
    for name in obj.objects:
        mesh = Mesh.from_vertices_and_faces(*obj.objects[name])
        mesh.name = name
        meshes.append(mesh)

# frames
origins = [
    [0, 0, 217],
    [24.512667, -6.66177, 400],
    [24.904867, -2.178893, 855],
    [145.743477, -12.750905, 869.151417],
    [443.020905, -38.51023, 816.506682],
    [519.30574, -44.271409, 816.486246],
]
x_axes = [[1, 0, 0], [1, 0, 0], [1, 0, 0], [0, -1, 0], [1, 0, 0], [0, 0, -1]]
y_axes = [[0, 0, 1], [0, 1, 0], [0, 1, 0], [1, -0, 0], [0, 1, 0], [1, 0, 0]]
frames = []
for i in range(len(origins)):
    frames.append(Frame(origins[i], x_axes[i], y_axes[i]))

# Create elements from meshes and add them to the model.
model = Model()
model.add_element(BlockElement(meshes[0], frame=Frame.worldXY(), name="Base"))
for i in range(1, len(meshes)):
    block = BlockElement(geometry=meshes[i], frame=frames[i - 1], name=f"Axis {i}")
    model.add_element(block)

for i in range(1, len(meshes) - 1):
    model.add_interaction_by_index(i, i + 1)

# Display geometry
geometry = model.get_interactions_lines()
for element in model.elements_list:
    geometry.append(element.frame)

model.print()
