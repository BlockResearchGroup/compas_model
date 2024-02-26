from compas.scene import Scene
from compas_model.elements import BlockElement
from compas_model.model import Model
from compas.geometry import Translation
from compas_rhino.objects import select_meshes
from compas_rhino.objects import find_object
from compas_rhino.conversions import mesh_to_compas


# Select Rhino Meshes and Convert them to compas mesh
guids = select_meshes()
meshes = []
for g in guids:
    meshes.append(mesh_to_compas(find_object(g).Geometry))

# Convert to Block Element
model = Model()
for idx, m in enumerate(meshes):
    block = BlockElement(m, name="block_"+str(idx))
    block.transform(Translation.from_vector([10,0,0]))
    model.add_element(block)

# Scene
scene = Scene()
for e in model.elements_list:
    scene.add(e)
scene.draw()
