from pathlib import Path

from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas_model.models import GridModel
from compas_viewer import Viewer
from compas_viewer.config import Config

# =============================================================================
# JSON file with the geometry of the model.
# =============================================================================
rhino_geometry: dict[str, list[any]] = json_load(Path("data/frame.json"))
lines: list[Line] = rhino_geometry["Model::Line::Segments"]
surfaces: list[Mesh] = rhino_geometry["Model::Mesh::Floor"]

# =============================================================================
# Model
# =============================================================================
model: GridModel = GridModel.from_lines_and_surfaces(columns_and_beams=lines, floor_surfaces=surfaces)

# =============================================================================
# Vizualize
# =============================================================================
config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000
viewer = Viewer(config=config)
viewer.scene.add(model.cell_network.points)
viewer.scene.add(model.cell_network.lines)
viewer.scene.add(model.cell_network.polygons)
viewer.show()
