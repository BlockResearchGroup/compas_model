from math import pi
from random import random

from compas.colors import Color
from compas.geometry import Box
from compas.geometry import Line
from compas.geometry import Rotation
from compas.geometry import Sphere
from compas.geometry import Translation
from compas_model.algorithms import is_intersection_segment_aabb
from compas_model.algorithms import is_intersection_sphere_aabb
from compas_viewer import Viewer

lines = []

box = Box()

line = Line.from_point_direction_length([0, 0, 0], [0, 0, 1], 1.0)
s1 = Sphere(point=[0, 0, 0], radius=0.1)
s2 = Sphere(point=[1.0, 0, 0], radius=0.1)
s3 = Sphere(point=[1.0, 0, 0], radius=0.49999)

T = Translation.from_vector([1, 0, 0])

for i in range(100):
    angles = random() * 2 * pi, random() * pi, random() * 2 * pi
    R = Rotation.from_euler_angles(angles)
    lines.append(line.transformed(T * R))

viewer = Viewer()
viewer.scene.add(box, show_faces=False)

for line in lines:
    viewer.scene.add(line, linecolor=Color.red() if is_intersection_segment_aabb(line, box) else Color.blue())

viewer.scene.add(s1, facecolor=Color.green() if is_intersection_sphere_aabb(s1, box) else Color.blue())
viewer.scene.add(s2, facecolor=Color.green() if is_intersection_sphere_aabb(s2, box) else Color.blue())
viewer.scene.add(s3, facecolor=Color.green() if is_intersection_sphere_aabb(s3, box) else Color.blue())

viewer.show()
