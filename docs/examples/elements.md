# Creating elements

Create a model, add a column, a beam and a plate to it, and show the model in the viewer. Adding the model to the viewer scene also adds all its elements, which are listed in the tree on the right.

![Creating elements](../assets/images/example_elements.png)

```bash
pip install "compas_model[viz]"
```

```python
from compas.geometry import Frame
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas_model.elements import BeamElement
from compas_model.elements import ColumnElement
from compas_model.elements import PlateElement
from compas_model.models import Model
from compas_viewer import Viewer

model = Model(name="elements")

# a column
column = ColumnElement(width=0.3, depth=0.3, height=3.0)
model.add_element(column)

# a beam, placed next to the column
frame = Frame([1.0, 0, 0.15], [0, 1, 0], [0, 0, 1])
beam = BeamElement(width=0.2, depth=0.3, length=2.0)
beam.transformation = Transformation.from_frame(frame)
model.add_element(beam)

# a plate, placed next to the beam
polygon = Polygon([[3.5, -1, 0], [4.5, -1, 0], [4.5, 1, 0], [3.5, 1, 0]])
plate = PlateElement(polygon, thickness=0.1)
model.add_element(plate)

# show the model in the viewer
viewer = Viewer()
viewer.scene.add(model)
viewer.show()
```
