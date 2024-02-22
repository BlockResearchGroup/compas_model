import pathlib

from compas.files import OBJ
from compas.datastructures import Mesh
from compas_model.model import Model
from compas_model.elements import BlockElement

# from compas_model.algorithms import collider

filepath = pathlib.Path(__file__).parent.parent / "data" / "cross_vault.obj"

obj = OBJ(filepath)
obj.read()

meshes = []
for name in obj.objects:  # type: ignore
    vertices, faces = obj.objects[name]  # type: ignore
    mesh = Mesh.from_vertices_and_faces(vertices, faces)
    mesh.name = name
    meshes.append(mesh)

model = Model()

for mesh in meshes:
    block = BlockElement(shape=mesh)
    model.add_element(block)

model.print()

# pairs = collider.get_collision_pairs(model)
# for item in pairs[:1]:
#     print(item)
