from compas.files import OBJ
# from compas_model.viewer import ViewerModel
from compas_model.elements import Block
from compas_model.model import Model
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