from compas.datastructures import Mesh
from compas.files import OBJ

# from compas_model.viewer import ViewerModel
from compas_model.elements import BlockElement
from compas_model.models import Model

# Read the OBJ file of Cross vault.
obj = OBJ("data/cross_vault.obj")
obj.read()

# Create elements from meshes and add them to the model.
model = Model()
elements = []
for name in obj.objects:
    mesh = Mesh.from_vertices_and_faces(*obj.objects[name])
    block = BlockElement(mesh)
    elements.append(block)
    model.add_element(block)
