from compas.geometry import Translation
from compas_model.elements import ColumnElement
from compas_model.models import Model
from compas_viewer import Viewer

# Create an element.
column: ColumnElement = ColumnElement(0.2, 0.2, 3)

# Element transformation can be set or modified as an attribute.
vectors : list[list[float]] = [
    [-3, -3, 0],
    [-3, 3, 0],
    [3, 3, 0],
    [3, -3, 0],
]

model = Model()
for v in vectors:
    column_copy = column.copy()
    column_copy.transformation = Translation.from_vector(v)
    model.add_element(column_copy)

# Vizualize.
viewer = Viewer()
for element in model.elements():
    viewer.scene.add(element.modelgeometry)
viewer.show()
