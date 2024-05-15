import pathlib

import compas
from compas.datastructures import Mesh
from compas.files import OBJ
from compas.geometry import Scale
from compas_model.algorithms import blockmodel_interfaces
from compas_model.elements import BlockElement
from compas_model.models import Model
from compas_model.viewers import BlockModelViewer

# =============================================================================
# Load block data
# =============================================================================

filepath = pathlib.Path(__file__).parent.parent / "data" / "crossvault_meshes_3DEC.json"

model3dec = compas.json_load(filepath)

for interaction in model3dec.interactions():
    print(interaction)

# # =============================================================================
# # Make model
# # =============================================================================

# model = Model()

# for mesh in meshes:
#     block = BlockElement(shape=mesh)
#     model.add_element(block)

# # model.transform(Scale.from_factors([0.025, 0.025, 0.025]))

# # =============================================================================
# # Compute interfaces
# # =============================================================================

# blockmodel_interfaces(model, nmax=7, tmax=1e-3, amin=1e-2)

# # =============================================================================
# # Boundary conditions
# # =============================================================================

# elements = sorted(model.elements(), key=lambda e: e.geometry.centroid().z)[:4]

# for element in elements:
#     element: BlockElement
#     element.is_support = True

# # =============================================================================
# # Export
# # =============================================================================

# here = pathlib.Path(__file__).parent
# compas.json_dump(meshes, here / "crossvault_meshes.json")

# # =============================================================================
# # Visualisation
# # =============================================================================

# viewer = BlockModelViewer()
# viewer.add(model, show_blockfaces=False, show_interfaces=True)
# viewer.show()
