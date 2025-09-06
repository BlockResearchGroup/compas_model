from pathlib import Path

from compas import json_dump
from compas import json_load
from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Transformation
from compas.geometry import Translation
from compas.geometry import Vector
from compas_model.elements import BeamElement
from compas_model.elements import ColumnElement
from compas_model.models import Model
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
    Line(points[0], points[4]),
    Line(points[1], points[5]),
    Line(points[2], points[6]),
    Line(points[3], points[7]),
    Line(points[4], points[5]),
    Line(points[6], points[7]),
    Line(points[5], points[6]),
    Line(points[7], points[4]),
]

mesh = Mesh.from_vertices_and_faces(points[4:], [[0, 1, 2, 3]])

# =============================================================================
# Serialize Geometry into a JSON file
# =============================================================================
model_input = {"Model::Line::Segments": lines, "Model::Mesh::Floor": [mesh]}
json_dump(model_input, Path("data/frame.json"))


# =============================================================================
# Load Geometry from JSON and Create Model
# =============================================================================
rhino_geometry = json_load(Path("data/frame.json"))
lines = rhino_geometry["Model::Line::Segments"]

model = Model()

# Add columns
columns = []
for i in range(4):
    column = ColumnElement(300, 300, lines[i].length)
    column.transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(lines[i].start))
    model.add_element(column)
    columns.append(column)

# Add beams
beams = []
for i in range(4, len(lines)):
    beam = BeamElement(width=300, depth=700, length=lines[i].length)
    point = lines[i].start
    xaxis = Vector.Zaxis().cross(lines[i].vector)
    yaxis = Vector.Zaxis()
    target_frame = Frame(point, xaxis, yaxis)
    X = Transformation.from_frame_to_frame(Frame.worldXY(), target_frame)
    T = Translation.from_vector([0, beam.depth * -0.5, 0])
    beam.transformation = X * T
    beam.extend(150)
    model.add_element(beam)
    beams.append(beam)

# Add interactions and modifiers
for column in columns:
    for beam in beams:
        model.add_interaction(column, beam)
        model.add_modifier(column, beam)  # column -> cuts -> beam

# =============================================================================
# Visualize Final Model
# =============================================================================
config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000

viewer = Viewer(config=config)
for element in model.elements():
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=True)
viewer.show()
