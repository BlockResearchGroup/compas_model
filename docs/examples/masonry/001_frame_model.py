from pathlib import Path

from compas import json_load
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Translation
from compas.geometry import Vector
from compas.geometry.transformation import Transformation
from compas.tolerance import TOL
from compas_model.elements import BeamTProfileElement
from compas_model.elements import CableElement
from compas_model.elements import ColumnSquareElement
from compas_model.models import BlockModel
from compas_model.models import Model
from compas_viewer import Viewer
from compas_viewer.config import Config

# =============================================================================
# JSON file with the geometry of the model.
# =============================================================================
rhino_geometry: dict[str, list[any]] = json_load(Path("data/frame.json"))
lines: list[Line] = rhino_geometry["Model::Line::Segments"]

# =============================================================================
# Model
# =============================================================================
model = Model()

# Add columns
for i in range(0, 4):
    column: ColumnSquareElement = ColumnSquareElement(300, 300, lines[i].length)
    column.transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame(lines[i].start))
    model.add_element(column)


# Add two beams
for i in range(4, len(lines) - 2):
    beam: BeamTProfileElement = BeamTProfileElement(width=300, height=700, step_width_left=75, step_height_left=150, length=lines[i].length)
    target_frame: Frame = Frame(lines[i].start, Vector.Zaxis().cross(lines[i].vector), Vector.Zaxis())
    beam.transformation = Transformation.from_frame_to_frame(Frame.worldXY(), target_frame) * Translation.from_vector([0, beam.height * 0.5, 0])
    beam.extend(150)
    model.add_element(beam)

# Add two cables
for i in range(6, len(lines)):
    cable: CableElement = CableElement(length=lines[i].length, radius=10)
    target_frame: Frame = Frame(lines[i].start, Vector.Zaxis().cross(lines[i].vector), Vector.Zaxis())
    cable.transformation = Transformation.from_frame_to_frame(Frame.worldXY(), target_frame) * Translation.from_vector([0, beam.height * 0.1, 0])
    cable.extend(200)
    model.add_element(cable)


# Add blocks, by moving them by the height of the first column.
blockmodel: BlockModel = BlockModel.from_barrel_vault(span=6000, length=6000, thickness=250, rise=600, vou_span=5, vou_length=5)
for block in blockmodel.elements():
    block.transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame([0, 0, lines[0].end[2]])) * block.transformation
    model.add_element(block)


# Add Interactions
for element in list(model.elements()):
    if isinstance(element, BeamTProfileElement):
        for block in blockmodel.elements():
            if isinstance(element, BeamTProfileElement):
                model.compute_contact(element, block)  # beam -> cuts -> block

for element in list(model.elements()):
    if isinstance(element, CableElement):
        for beam in list(model.elements()):
            if isinstance(beam, BeamTProfileElement):
                model.compute_contact(element, beam)  # cable -> cuts -> beam

# =============================================================================
# Vizualize
# =============================================================================
TOL.lineardeflection = 100
config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000
viewer = Viewer(config=config)
for element in list(model.elements()):
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=False)
viewer.show()
