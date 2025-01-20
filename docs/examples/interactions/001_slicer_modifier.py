from compas.geometry import Rotation
from compas.geometry import Translation
from compas_model.elements import BeamElement
from compas_model.interactions import SlicerModifier
from compas_model.models import Model
from compas_viewer import Viewer

# Create an element.
beam0: BeamElement = BeamElement(0.2, 0.3, 3, name="beam0")
beam1 : BeamElement = beam0.copy()
beam1.name = "beam1"

# Element transformation can be set or modified as an attribute.
beam0.transformation = Rotation.from_axis_and_angle([0, 1, 0], 3.14/2, beam0.axis.midpoint)
beam0.transformation = Translation.from_vector([0, 0, 1.5])* beam0.transformation # Rotate then translate

# But the transformation is applied when beam.modelgeometry is computed.
model = Model()
model.add_element(beam0)
model.add_element(beam1)

model.add_interaction(beam0, beam1)
model.add_modifier(beam0, beam1, SlicerModifier)

# Vizualize.
viewer = Viewer()
for element in model.elements():
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=True)
viewer.show()
