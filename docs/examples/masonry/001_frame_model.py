from pathlib import Path

from compas import json_load
from compas.geometry import Frame
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Vector
from compas_model.models import Model
from compas_model.models import BlockModel
from compas_model.elements import ColumnSquareElement
from compas_model.elements import BeamTProfileElement
from compas_model.elements import BlockElement
from compas.geometry.transformation import Transformation
from compas.geometry import Translation
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
model = Model()

# Add columns
for i in range(0, 4):
    line : Line = lines[i]
    column: ColumnSquareElement = ColumnSquareElement(300,300, line.length)
    target_frame : Frame = Frame(line.start)
    xform : Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), target_frame)
    column.transformation = xform
    model.add_element(column)



# Add two beams
for i in range(4,len(lines)):
    line : Line = lines[i]
    beam: BeamTProfileElement = BeamTProfileElement(300,700,100,100,150,150, line.length)
    target_frame : Frame = Frame(line.start, Vector.Zaxis().cross(line.vector), Vector.Zaxis())
    xform_offset : Transformation = Translation.from_vector([0, beam.height*0.5, 0])
    xform_to_beam : Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), target_frame)
    beam.transformation = xform_to_beam * xform_offset
    beam.extend(150)
    model.add_element(beam)


# Add blocks
blockmodel : BlockModel = BlockModel.from_barrel_vault(6000, 6000,250, 600, 5,5)
barrel_vault_elements : list[BlockElement] = list(blockmodel.elements())
for block in barrel_vault_elements:
    xform : Transformation = Transformation.from_frame_to_frame(Frame.worldXY(), Frame([0,0,lines[0].end[2]]))
    block.transformation = xform * block.transformation
    model.add_element(block)

# =============================================================================
# Vizualize
# =============================================================================
config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000
viewer = Viewer(config=config)
for element in list(model.elements()):
    viewer.scene.add(element.modelgeometry)
viewer.show()