from compas_model.elements import ColumnHeadCrossElement
from compas_viewer import Viewer

column = ColumnHeadCrossElement()


viewer = Viewer()
viewer.scene.add(column.compute_elementgeometry())
viewer.show()
