from pathlib import Path

from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas_model.elements import ColumnHeadCrossElement
from compas_model.elements import ColumnSquareElement
from compas_model.elements import ScrewElement
from compas_model.interactions import BooleanModifier
from compas_model.interactions import SlicerModifier
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
model: GridModel = GridModel.from_lines_and_surfaces(columns_and_beams=lines, floor_surfaces=surfaces, tolerance=3)

# =============================================================================
# Add Elements to CellNetwork Edge
# =============================================================================
column_head = ColumnHeadCrossElement(width=150, depth=150, height=300, offset=210)
column_square = ColumnSquareElement(width=300, depth=300)
model.add_column_head(column_head, model.columns[0])
model.add_column(column_square, model.columns[0])

# =============================================================================
# Add Interaction
# =============================================================================
model.add_contact(column_head, column_square)
# model.add_interaction_columnhead_and_column(model.columns[0], SlicerModifier)
# model.add_interaction_columnhead_and_column(model.columns[0], BooleanModifier, elements=[ScrewElement(20, 6, 400)], apply_to_start=False)

# =============================================================================
# Vizualize
# =============================================================================
viewer = Viewer()
viewer.scene.add(model.geometry)
viewer.show()
