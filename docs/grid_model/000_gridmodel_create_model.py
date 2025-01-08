from pathlib import Path

from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas_model.models import GridModel

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
# Vizualize
# =============================================================================
try:
    from compas_viewer import Viewer

    viewer = Viewer()
    viewer.scene.add(model.points)
    viewer.scene.add(model.lines)
    viewer.scene.add(model.polygons)
    viewer.show()
except ImportError:
    print("The compas_viewer package is not installed.")
    print("Please install it by running 'pip install compas_viewer'.")
    print("Then, try to run this script again.")
