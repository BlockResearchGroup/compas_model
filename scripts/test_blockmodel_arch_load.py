import pathlib

import compas
from compas_model.models import Model
from compas_model.viewers import BlockModelViewer

here = pathlib.Path(__file__).parent
model: Model = compas.json_load(here / "blockmodel_arch.json")

viewer = BlockModelViewer()
viewer.add(
    model,
    show_blockfaces=False,
    show_interfaces=True,
    show_contactforces=True,
    scale_compression=2,
    scale_friction=2,
    scale_tension=2,
    scale_resultant=2,
)
viewer.show()
