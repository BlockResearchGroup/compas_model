from compas.geometry import Polygon
from compas.geometry import Translation
from compas_model.elements import BeamElement
from compas_model.elements import PlateElement
from compas_model.models import Model
from compas_viewer import Viewer

beam1 = BeamElement(0.2, 0.3, 3)
beam2 = BeamElement(0.2, 0.3, 3)
beam3 = BeamElement(0.2, 0.3, 3)
beam4 = BeamElement(0.2, 0.3, 3)

beam1.transformation = Translation.from_vector([3, 3, 0])
beam2.transformation = Translation.from_vector([-3, 3, 0])
beam3.transformation = Translation.from_vector([-3, -3, 0])
beam4.transformation = Translation.from_vector([3, -3, 0])


points: list[list[float]] = [
    [-3, -3, 0],
    [-3, 3, 0],
    [3, 3, 0],
    [3, -3, 0],
]
polygon: Polygon = Polygon(points)
plate = PlateElement(polygon=polygon, thickness=0.2)
plate.transformation = Translation.from_vector([0, 0, 3])

model = Model()
group = model.add_group(name="Beams")
model.add_element(beam1, parent=group)
model.add_element(beam2, parent=group)
model.add_element(beam3, parent=group)
model.add_element(beam4, parent=group)
model.add_element(plate)

# Vizualize.
viewer = Viewer()
viewer.scene.add(model)
viewer.show()
