# Element tree

Organise elements in a hierarchy. Each level of a building is a group in the element tree of the model, and its columns and slab are the children of the level. The tree is shown in the sidebar of the viewer. Click a level to select all its elements.

![Element tree](../assets/images/example_tree.png)

```bash
pip install "compas_model[viz]"
```

```python
from compas.geometry import Polygon
from compas.geometry import Translation
from compas_model.elements import ColumnElement
from compas_model.elements import Group
from compas_model.elements import PlateElement
from compas_model.models import Model
from compas_viewer import Viewer

H = 3.0  # column height
S = 6.0  # distance between the columns
W = 0.3  # column width
T = 0.2  # slab thickness
L = H + T  # level height, the columns of a level stand on the slab below

model = Model(name="building")

for index in range(4):
    # a level is a group, all its elements are positioned relative to the level
    level = Group(name=f"level {index}")
    level.transformation = Translation.from_vector([0, 0, index * L])
    model.add_element(level)

    for x, y in [(0, 0), (S, 0), (S, S), (0, S)]:
        column = ColumnElement(width=W, depth=W, height=H, name="column")
        column.transformation = Translation.from_vector([x, y, 0])
        model.add_element(column, parent=level)

    polygon = Polygon(
        [
            [-W / 2, -W / 2, L],
            [S + W / 2, -W / 2, L],
            [S + W / 2, S + W / 2, L],
            [-W / 2, S + W / 2, L],
        ]
    )
    slab = PlateElement(polygon, thickness=T, name="slab")
    model.add_element(slab, parent=level)

viewer = Viewer()
viewer.scene.add(model)
viewer.show()
```
