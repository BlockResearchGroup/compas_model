from pathlib import Path

from compas import json_dump
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Point
from compas_viewer import Viewer
from compas_viewer.config import Config

# =============================================================================
# Create Geometry
# =============================================================================

points = [
    Point(-3000, -3000, 0),
    Point(-3000, 3000, 0),
    Point(3000, 3000, 0),
    Point(3000, -3000, 0),
    Point(-3000, -3000, 3800),
    Point(-3000, 3000, 3800),
    Point(3000, 3000, 3800),
    Point(3000, -3000, 3800),
]

lines = [
    Line(points[0], points[0 + 4]),
    Line(points[1], points[1 + 4]),
    Line(points[2], points[2 + 4]),
    Line(points[3], points[3 + 4]),
    Line(points[4], points[5]),
    Line(points[6], points[7]),
    Line(points[5], points[6]),
    Line(points[7], points[4]),
]

mesh = Mesh.from_vertices_and_faces(points[4:], [[0, 1, 2, 3]])


# =============================================================================
# Serialize the Frame into a JSON file.
# =============================================================================

model_input: dict[str, list[any]] = {"Model::Line::Segments": lines, "Model::Mesh::Floor": [mesh]}
json_dump(model_input, Path("data/frame.json"))

# =============================================================================
# Vizualize
# =============================================================================

config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000
viewer = Viewer(config=config)
viewer.scene.add(lines)
viewer.scene.add(mesh)
viewer.show()