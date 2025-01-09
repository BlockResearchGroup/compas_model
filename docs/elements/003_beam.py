from compas_model.elements import BeamSquareElement
from compas_viewer import Viewer

beam = BeamSquareElement()


viewer = Viewer()
viewer.scene.add(beam.compute_elementgeometry())
viewer.show()
