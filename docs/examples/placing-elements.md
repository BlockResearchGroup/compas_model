# Placing elements

Place elements precisely relative to each other. A 9 m x 9 m floor bay has four columns, four beams and a flat plate on top. Beams rest on the columns and the plate rests on the beams, with all member ends flush with the faces of their supports.

![Placing elements](../assets/images/example_placing.png)

```bash
pip install "compas_model[viz]"
```

```python
from compas.geometry import Frame
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Translation
from compas_model.elements import BeamElement
from compas_model.elements import ColumnElement
from compas_model.elements import PlateElement
from compas_model.models import Model
from compas_viewer import Viewer

S = 9.0  # bay size, distance between column axes
H = 3.0  # column height
W = 0.3  # column and beam width
D = 0.6  # beam depth
T = 0.2  # plate thickness

model = Model(name="floor")

# columns at the corners
for x, y in [(0, 0), (S, 0), (S, S), (0, S)]:
    column = ColumnElement(width=W, depth=W, height=H)
    column.transformation = Translation.from_vector([x, y, 0])
    model.add_element(column)

# beams along x rest on the columns, ends flush with the outer column faces
for y in (0, S):
    frame = Frame([-W / 2, y, H + D / 2], [0, 1, 0], [0, 0, 1])
    beam = BeamElement(width=W, depth=D, length=S + W)
    beam.transformation = Transformation.from_frame(frame)
    model.add_element(beam)

# beams along y span between the faces of the beams along x
for x in (0, S):
    frame = Frame([x, W / 2, H + D / 2], [-1, 0, 0], [0, 0, 1])
    beam = BeamElement(width=W, depth=D, length=S - W)
    beam.transformation = Transformation.from_frame(frame)
    model.add_element(beam)

# a flat plate rests on the beams, flush with their outer faces
z = H + D + T
polygon = Polygon(
    [
        [-W / 2, -W / 2, z],
        [S + W / 2, -W / 2, z],
        [S + W / 2, S + W / 2, z],
        [-W / 2, S + W / 2, z],
    ]
)
plate = PlateElement(polygon, thickness=T)
model.add_element(plate)

viewer = Viewer()
viewer.scene.add(model)
viewer.show()
```
