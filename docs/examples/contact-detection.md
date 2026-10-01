# Contact detection

Detect the contacts between elements. The 184 blocks of a cross vault are shown as wireframe, with the contacts that were detected between them as filled polygons. The blocks are stored in `data/cross_vault.obj` in the repository, so run the script from the root of the repository.

![Contact detection](../assets/images/example_contacts.png)

```bash
pip install "compas_model[viz]" compas_dem
```

```python
from compas.colors import Color
from compas.datastructures import Mesh
from compas.files import OBJ
from compas_dem.elements import Block
from compas_dem.models import BlockModel
from compas_viewer import Viewer

# the blocks of the cross vault are objects in an OBJ file
obj = OBJ("data/cross_vault.obj")
obj.read()

model = BlockModel(name="cross vault")

for vertices, faces in obj.objects.values():
    mesh = Mesh.from_vertices_and_faces(vertices, faces)
    model.add_element(Block.from_mesh(mesh))

# find the contacts between the blocks
model.compute_contacts(tolerance=0.01, minimum_area=0.1)

viewer = Viewer()
viewer.config.renderer.show_grid = False

# show the blocks as wireframe
modelobject = viewer.scene.add(model)
for blockobject in modelobject.children:
    blockobject.show_faces = False

# show the contacts as filled polygons, in a group of their own
contacts = viewer.scene.add_group(name="contacts")

for contact in model.contacts():
    viewer.scene.add(contact.polygon, parent=contacts, facecolor=Color.from_hex("#f2d500"), show_lines=False)

viewer.show()
```
