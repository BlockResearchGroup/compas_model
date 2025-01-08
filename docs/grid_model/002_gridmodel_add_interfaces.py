from pathlib import Path

from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Polygon
from compas_model.elements import BeamSquareElement
from compas_model.elements import ColumnHeadCrossElement
from compas_model.elements import ColumnSquareElement
from compas_model.elements import PlateElement
from compas_model.elements import ScrewElement
from compas_model.interactions import BooleanModifier
from compas_model.interactions import SlicerModifier
from compas_model.models import GridModel

# =============================================================================
# JSON file with the geometry of the model. Datasets: frame.json, crea_4x4.json
# =============================================================================
rhino_geometry: dict[str, list[any]] = json_load(Path("data/crea_4x4.json"))
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
# =============================================================================
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
# Add Interaction between Column and Column Head.
# =============================================================================
for edge in model.columns:
    model.add_interaction_columnhead_and_column(edge, SlicerModifier)
    model.add_interaction_columnhead_and_column(edge, BooleanModifier, elements=[ScrewElement(20, 6, 400)], apply_to_start=False, apply_to_end=True)

# =============================================================================
# Add Interaction between Beam and Column Head.
# =============================================================================
for edge in model.beams:
    model.add_interaction_columnhead_and_beam(edge, SlicerModifier)

# =============================================================================
# Add Interaction between Floor and Column Head.
# =============================================================================
for vertex, plates_and_faces in model.vertex_to_plates_and_faces.items():
    model.add_interaction_columnhead_and_floor(vertex, plates_and_faces, SlicerModifier)


# =============================================================================
# Vizualize
# =============================================================================
try:
    from compas_viewer import Viewer

    viewer = Viewer()
    viewer.scene.add(model.geometry)
    viewer.show()
except ImportError:
    print("The compas_viewer package is not installed.")
    print("Please install it by running 'pip install compas_viewer'.")
    print("Then, try to run this script again.")
