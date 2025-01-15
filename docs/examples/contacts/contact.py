from pathlib import Path

from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Polygon
from compas.tolerance import TOL
from compas_model.elements import ColumnHeadCrossElement
from compas_model.elements import PlateElement
from compas_model.models import Model
from compas_viewer import Viewer
from compas_viewer.config import Config

# =============================================================================
# Model
# =============================================================================
model: Model = Model()

# =============================================================================
# Add Elements to CellNetwork Edge
# =============================================================================


column_head = ColumnHeadCrossElement(width=0.150, depth=0.150, height=0.300, offset=0.210)
plate: PlateElement = PlateElement(Polygon([[-2.850, -2.850, 0], [-2.850, 2.850, 0], [2.850, 2.850, 0], [2.850, -2.850, 0]]), 0.200)

model.add_element(column_head)
model.add_element(plate)

# =============================================================================
# Add Interaction
# TODO: Check with other default ColumnHead Planes to Debug compas_occ.
# =============================================================================
model.compute_contact(column_head, plate)

# =============================================================================
# Vizualize
# =============================================================================
TOL.lineardeflection = 1000

config = Config()
viewer = Viewer(config=config)
for element in model.elements():
    viewer.scene.add(element.modelgeometry)
# viewer.scene.add(beam1.axis.midpoint)
# viewer.scene.add(beam1.axis)

viewer.show()
