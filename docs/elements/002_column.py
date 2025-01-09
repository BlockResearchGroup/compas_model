from compas_model.elements import ColumnSquareElement
from compas_viewer import Viewer

column = ColumnSquareElement()


viewer = Viewer()
viewer.scene.add(column.compute_elementgeometry())
viewer.show()
