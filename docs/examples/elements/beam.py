from compas.tolerance import TOL
from compas_model.elements import BeamTProfileElement
from compas_viewer import Viewer
from compas_viewer.config import Config

scale = 1
beam: BeamTProfileElement = BeamTProfileElement(
    width=0.2 * scale,
    height=0.3 * scale,
    step_height_left=0.1 * scale,
    step_height_right=0.1 * scale,
    step_width_left=0.05 * scale,
    step_width_right=0.05 * scale,
    length=6 * scale,
)

TOL.lineardeflection = 1000

config = Config()

config.camera.target = [0, 0.1 * scale, 0]
config.camera.position = [0, -0.2 * scale, 7 * scale]
config.camera.near = 0.1 * scale
config.camera.far = 10 * scale
viewer = Viewer(config=config)
viewer.scene.add(beam.elementgeometry)

viewer.show()
