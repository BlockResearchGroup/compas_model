from compas_model.elements import CableElement
from compas_viewer import Viewer
from compas_viewer.config import Config

scale = 1
column: CableElement = CableElement()


config = Config()

config.camera.target = [0, 0.1 * scale, 0]
config.camera.position = [0, -0.2 * scale, 7 * scale]
config.camera.near = 0.1 * scale
config.camera.far = 10 * scale
viewer = Viewer(config=config)
viewer.scene.add(column.elementgeometry)
viewer.scene.add(column.axis)

viewer.show()
