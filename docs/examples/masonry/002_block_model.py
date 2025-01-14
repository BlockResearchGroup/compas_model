from compas.tolerance import TOL
from compas_model.models import BlockModel
from compas_viewer.config import Config
from compas_viewer.viewer import Viewer

model: BlockModel = BlockModel.from_barrel_vault(span=6000, length=6000, thickness=250, rise=600, vou_span=5, vou_length=5)


TOL.lineardeflection = 1000

config = Config()
config.camera.target = [0, 0, 100]
config.camera.position = [10000, -10000, 10000]
config.camera.near = 10
config.camera.far = 100000
viewer = Viewer(config=config)
for element in list(model.elements()):
    viewer.scene.add(element.modelgeometry, hide_coplanaredges=True)
viewer.show()
