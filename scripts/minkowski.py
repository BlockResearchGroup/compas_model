import time

from compas.colors import Color
from compas.geometry import Polygon
from compas_model.algorithms.collision2 import is_collision2
from compas_viewer import Viewer

# =============================================================================
# Compute
# =============================================================================

A = Polygon.from_rectangle([1, 0, 0], 1, 1)
B = Polygon.from_sides_and_radius_xy(5, 1).translated([2.5, 0, 0])

t0 = time.time()

result, C = is_collision2(A, B, return_diff=True)
print(result)

t1 = time.time()

print(t1 - t0)

# =============================================================================
# Viz
# =============================================================================

viewer = Viewer()

viewer.scene.add(A, facecolor=Color.red(), opacity=0.5)
viewer.scene.add(B, facecolor=Color.blue(), opacity=0.5)
viewer.scene.add(C, facecolor=Color.cyan(), opacity=0.5)

viewer.show()
