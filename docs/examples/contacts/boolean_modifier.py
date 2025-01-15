from math import pi

from compas.geometry.rotation import Rotation
from compas.geometry.translation import Translation
from compas.tolerance import TOL
from compas_model.elements import BeamSquareElement
from compas_model.models import Model
from compas_viewer import Viewer
from compas_viewer.config import Config

# =============================================================================
# Model
# =============================================================================

model = Model()

beam0: BeamSquareElement = BeamSquareElement(
    width=0.2,
    depth=0.3,
    length=6,
)

beam1: BeamSquareElement = BeamSquareElement(
    width=0.2,
    depth=0.3,
    length=6,
)

beam_node = model.add_element(beam0)
model.add_element(beam1, parent=beam_node)
rotation: Rotation = Rotation.from_axis_and_angle([0, 1, 0], pi / 4, point=beam1.axis.midpoint)
translation = Translation.from_vector([0, 0.1, 0])
beam1.transformation = translation * rotation

model.compute_contact(beam0, beam1)  # this method works when Beam class has modifier method

# =============================================================================
# Vizualize
# =============================================================================
TOL.lineardeflection = 1000

config = Config()
viewer = Viewer(config=config)
for element in model.elements():
    viewer.scene.add(element.modelgeometry)
viewer.show()
