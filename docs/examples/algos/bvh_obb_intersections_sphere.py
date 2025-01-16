import random
import time

from compas.colors import Color
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Sphere
from compas_model.algorithms import BVH
from compas_model.algorithms import OBBNode
from compas_model.geometry import intersection_ray_triangle
from compas_viewer import Viewer

sphere = Sphere(5)
mesh = sphere.to_mesh(triangulated=True, u=32, v=32)

print(mesh.number_of_faces())

# =============================================================================
# Lines
# =============================================================================

lines = []

for i in range(100):
    direction = [
        random.choice([-1, +1]) * random.random(),
        random.choice([-1, +1]) * random.random(),
        random.choice([-1, +1]) * random.random(),
    ]
    lines.append(
        Line.from_point_direction_length(
            point=[0, 0, 0],
            direction=direction,
            length=7,
        )
    )

# =============================================================================
# BVH
# =============================================================================

t0 = time.time()

bvh = BVH.from_mesh(mesh, nodetype=OBBNode, leafsize=3)

print(time.time() - t0)

# =============================================================================
# Intersections
# =============================================================================

count = 0
boxes = []
points = []

t0 = time.time()

for line in lines:
    for node in bvh.intersect_line(line):
        if not node.is_leaf:
            continue
        for index, centroid, triangle in node.objects:
            result = intersection_ray_triangle(line, triangle)
            if result is None:
                continue
            boxes.append(node.box)
            points.append(Point(*result))
            count += 1

print(time.time() - t0)

print(count)

# =============================================================================
# Viz
# =============================================================================

viewer = Viewer()
viewer.scene.add(mesh, show_faces=True)
viewer.scene.add(lines, linecolor=Color.blue(), linewidth=2)
# viewer.scene.add(boxes, facecolor=Color.green(), opacity=0.5)
viewer.scene.add(points, pointcolor=Color.red(), pointsize=20)
viewer.show()
