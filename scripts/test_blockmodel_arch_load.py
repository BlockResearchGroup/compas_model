import compas
from compas_model.models import Model
from compas_model.viewers import BlockModelViewer

model: Model = compas.json_load("test.json")

viewer = BlockModelViewer(model)
viewer.show()
