from compas.geometry import Rotation
from compas.geometry import Translation
from compas_model.elements import BeamElement
from compas_model.interactions import BooleanModifier
from compas_model.models import Model
from compas_viewer import Viewer

# Create an element.
beam0: BeamElement = BeamElement(0.2, 0.3, 3, name="beam0")
beam1: BeamElement = beam0.copy()
beam1.name = "beam1"

# Element transformation can be set or modified as an attribute.
R = Rotation.from_axis_and_angle([0, 1, 0], 3.14 / 2, beam0.center_line.midpoint)
T = Translation.from_vector([0, 0, 1.5])
beam0.transformation = T * R  # Rotate then translate

# But the transformation is applied when beam.modelgeometry is computed.
model = Model()
model.add_element(beam0)
model.add_element(beam1)

model.add_interaction(beam1, beam0)
model.add_modifier(beam1, beam0, BooleanModifier)

# Vizualize.
viewer = Viewer()
for element in model.elements():
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=True)
viewer.show()
