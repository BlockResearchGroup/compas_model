from pathlib import Path

from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Line
from compas_model.elements import BeamSquareElement
from compas_model.elements import ColumnHeadCrossElement
from compas_model.models import GridModel
from compas_viewer import Viewer
from compas_viewer.config import Config

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

# =============================================================================
# Add Elements to CellNetwork Edge
# =============================================================================
edges_beams = list(model.cell_network.edges_where({"is_beam": True}))

column_head = ColumnHeadCrossElement(width=150, depth=150, height=300, offset=210)
beam = BeamSquareElement(width=300, depth=300)

model.add_column_head(column_head, edges_beams[0])
model.add_beam(beam, edges_beams[0])

# =============================================================================
# Add Interaction
# =============================================================================
model.add_contact(column_head, beam)

# =============================================================================
# Vizualize
# =============================================================================
config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000
viewer = Viewer(config=config)
viewer.scene.add(model.cell_network.lines)
viewer.scene.add(model.cell_network.polygons)
viewer.scene.add(model.geometry)
viewer.show()
