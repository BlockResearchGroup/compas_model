from math import radians

from compas.colors import Color
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Transformation
from compas.geometry import Vector
from compas_model.algorithms.intersections import intersections_line_aabb
from compas_model.algorithms.intersections import intersections_line_box
from compas_model.algorithms.intersections import intersections_ray_box
from compas_model.algorithms.intersections import is_intersection_box_box
from compas_model.algorithms.intersections import is_intersection_line_box
from compas_viewer import Viewer

# line = Line.from_point_direction_length([-10, 0, -5], [0, 0, 1], 10)
# box = Box(8, 5, 3)

# for i in range(200):
#     line.start.x += 0.1
#     print(is_intersection_line_box(line, box))

# viewer = Viewer()
# viewer.scene.add(line, linewidth=2, linecolor=Color.blue())
# viewer.scene.add(box, facecolor=Color.red(), opacity=0.5)
# viewer.show()

# line = Line.from_point_direction_length([3, 1, 1], [0.3, 1, 1], 10)
# box = Box(1, 1, 1, frame=Frame([3, 0, 0], [1, 0, 0], [0, 1, 0.5]))

# line = Line([1, 0, 0], [0, 0, 1])
# box = Box()

# count, points = intersections_line_aabb(line, box)

# print(count)
# print(points)

# viewer = Viewer()
# viewer.scene.add(line, linewidth=2, linecolor=Color.blue())
# viewer.scene.add(box, facecolor=Color.red(), opacity=0.5)
# viewer.scene.add(points, pointcolor=Color.green(), pointsize=20)
# viewer.show()

b1 = Box()
b2 = Box(1, 1, 1, Frame([1.1, 0, 0])).rotated(radians(30))

print(is_intersection_box_box(b1, b2))

viewer = Viewer()
viewer.scene.add(b1, facecolor=Color.red(), opacity=0.5)
viewer.scene.add(b2, facecolor=Color.blue(), opacity=0.5)
viewer.show()
