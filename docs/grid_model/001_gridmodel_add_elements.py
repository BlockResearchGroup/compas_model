from pathlib import Path

from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Polygon
from compas_model.elements import BeamSquareElement
from compas_model.elements import ColumnHeadCrossElement
from compas_model.elements import ColumnSquareElement
from compas_model.elements import PlateElement
from compas_model.models import GridModel
from compas_viewer import Viewer

# =============================================================================
# JSON file with the geometry of the model.
# =============================================================================
rhino_geometry: dict[str, list[any]] = json_load(Path("data/frame.json"))
lines: list[Line] = rhino_geometry["Model::Line::Segments"]
surfaces: list[Mesh] = rhino_geometry["Model::Mesh::Floor"]

# =============================================================================
# Model
# =============================================================================
model: GridModel = GridModel.from_lines_and_surfaces(columns_and_beams=lines, floor_surfaces=surfaces, tolerance=3)

# =============================================================================
# Add Column Heads
# =============================================================================
column_head: ColumnHeadCrossElement = ColumnHeadCrossElement(width=150, depth=150, height=300, offset=210)
for edge in model.columns:
    model.add_column_head(column_head, edge)

# =============================================================================
# Add Columns
# =============================================================================)
column_square: ColumnSquareElement = ColumnSquareElement(width=300, depth=300)
for edge in model.columns:
    model.add_column(column_square, edge)

# =============================================================================
# Add Beams
# =============================================================================
beam_square: BeamSquareElement = BeamSquareElement(width=300, depth=300)
for edge in model.beams:
    model.add_beam(beam_square, edge)

# =============================================================================
# Add Plates
# =============================================================================
plate: PlateElement = PlateElement(Polygon([[-2850, -2850, 0], [-2850, 2850, 0], [2850, 2850, 0], [2850, -2850, 0]]), 200)
for face in model.floors:
    model.add_floor(plate, face)

# =============================================================================
# Vizualize
# =============================================================================
viewer = Viewer()
viewer.scene.add(model.geometry)
viewer.show()
