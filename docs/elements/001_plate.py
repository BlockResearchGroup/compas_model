from compas_model.elements import PlateElement
from compas_viewer import Viewer

plate = PlateElement()


viewer = Viewer()
viewer.scene.add(plate.compute_elementgeometry())
viewer.show()
