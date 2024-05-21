import pathlib

import compas
from compas.geometry import Box
from compas_model.algorithms import blockmodel_interfaces
from compas_model.analysis import cra_penalty_solve
from compas_model.elements import BlockElement
from compas_model.elements import BlockGeometry
from compas_model.models import Model
from compas_model.viewers import BlockModelViewer

# =============================================================================
# Geometry
# =============================================================================

base = Box(1, 1, 1)

boxes = []
for i in range(10):
    box = base.translated([i * 0.13, 0, i * base.zsize])
    boxes.append(box)

# =============================================================================
# Assembly
# =============================================================================

model = Model()

for box in boxes:
    model.add_element(BlockElement(shape=BlockGeometry.from_shape(box)))

# =============================================================================
# Interfaces
# =============================================================================

blockmodel_interfaces(model, amin=1e-2, tmax=1e-2)

# =============================================================================
# Boundary conditions
# =============================================================================

elements: list[BlockElement] = sorted(model.elements(), key=lambda e: e.geometry.centroid().z)[:1]

for element in elements:
    element.is_support = True

# =============================================================================
# Equilibrium
# =============================================================================

cra_penalty_solve(model)

# =============================================================================
# Export
# =============================================================================

filepath = pathlib.Path(__file__).parent / "000_dem_stack.json"

compas.json_dump(model, filepath)

# =============================================================================
# Viz
# =============================================================================

viewer = BlockModelViewer()
viewer.renderer.camera.target = [0, 0, 5]
viewer.renderer.camera.position = [0, -15, 7]

viewer.add_blockmodel(model, show_blockfaces=False, show_interfaces=True, show_contactforces=True)
viewer.show()
