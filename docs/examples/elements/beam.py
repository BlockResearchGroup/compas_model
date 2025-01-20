from compas.datastructures import Mesh
from compas.geometry import Rotation
from compas.geometry import Translation
from compas_model.elements import BeamElement
from compas_model.models import Model
from compas_viewer import Viewer

# Create an element.
beam = BeamElement(0.2, 0.3, 3)

# Element transformation can be set or modified as an attribute.
beam.transformation = Rotation.from_axis_and_angle([0, 1, 0], 3.14 / 2, beam.center_line.midpoint)
beam.transformation = Translation.from_vector([0, 0, 1.5]) * beam.transformation  # Rotate then translate

# But the transformation is applied when beam.modelgeometry is computed.
model = Model()
model.add_element(beam)
mesh_in_element_space: Mesh = beam.elementgeometry
mesh_in_model_space: Mesh = beam.modelgeometry

# Vizualize.
viewer = Viewer()
viewer.scene.add(mesh_in_element_space)
viewer.scene.add(mesh_in_model_space)
viewer.show()
