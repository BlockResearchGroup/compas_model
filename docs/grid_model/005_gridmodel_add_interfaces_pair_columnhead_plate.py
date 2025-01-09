from pathlib import Path

from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Polygon
from compas_model.elements import ColumnHeadCrossElement
from compas_model.elements import PlateElement
from compas_model.models import GridModel
from compas_viewer import Viewer

# =============================================================================
# JSON file with the geometry of the model. Datasets: frame.json, crea_4x4.json
# =============================================================================
rhino_geometry: dict[str, list[any]] = json_load(Path("data/frame.json"))
lines: list[Line] = rhino_geometry["Model::Line::Segments"]
surfaces: list[Mesh] = rhino_geometry["Model::Mesh::Floor"]

# =============================================================================
# Model
# =============================================================================
model: GridModel = GridModel.from_lines_and_surfaces(columns_and_beams=lines, floor_surfaces=surfaces)
edges_beams = list(model.cell_network.edges_where({"is_beam": True}))  # Order as in the model
faces_floors = list(model.cell_network.faces_where({"is_floor": True}))  # Order as in the model

# =============================================================================
# Add Elements to CellNetwork Edge
# =============================================================================
column_head = ColumnHeadCrossElement(width=150, depth=150, height=300, offset=210)
plate: PlateElement = PlateElement(Polygon([[-2850, -2850, 0], [-2850, 2850, 0], [2850, 2850, 0], [2850, -2850, 0]]), 200)

model.add_column_head(column_head, edges_beams[0])
model.add_floor(plate, faces_floors[0])

# =============================================================================
# Add Interaction
# =============================================================================
model.add_contact(column_head, plate)

# =============================================================================
# Vizualize
# =============================================================================
viewer = Viewer()
viewer.scene.add(model.cell_network.lines)
viewer.scene.add(model.cell_network.polygons)
viewer.scene.add(model.geometry)
viewer.show()
