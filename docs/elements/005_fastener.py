from compas_model.elements import ScrewElement
from compas_viewer import Viewer

screw = ScrewElement()


viewer = Viewer()
viewer.scene.add(screw.compute_elementgeometry())
viewer.show()
