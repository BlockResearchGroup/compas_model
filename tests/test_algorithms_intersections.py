from math import pi
from pytest import mark
from random import random

from compas.geometry import Box
from compas.geometry import Line
from compas.geometry import Rotation
from compas.geometry import Sphere
from compas_model.geometry import intersections_line_aabb
from compas_model.geometry import is_intersection_sphere_aabb

# from compas_model.algorithms.intersections import intersections_line_box
# from compas_model.algorithms.intersections import intersections_ray_aabb
# from compas_model.algorithms.intersections import intersections_ray_box


@mark.parametrize(
    ["sphere", "result"],
    [
        [Sphere(point=[0, 0, 0], radius=0.1), True],
        [Sphere(point=[1.0, 0, 0], radius=0.5), True],
        [Sphere(point=[1.0, 0, 0], radius=0.4999), False],
        [Sphere(point=[1.0, 0, 0], radius=0.1), False],
    ],
)
def test_is_intersection_sphere_aabb_known(sphere, result):
    box = Box()
    assert is_intersection_sphere_aabb(sphere, box) is result


@mark.parametrize(
    ["line", "known"],
    [
        [Line([0, 0, 0], [1, 0, 0]), (2, [[-1, 0, 0], [1, 0, 0]])],
        [Line([0, 0, 0], [-1, 0, 0]), (2, [[1, 0, 0], [-1, 0, 0]])],
        [Line([0, 0, 0], [0, 1, 0]), (2, [[0, -1, 0], [0, 1, 0]])],
        [Line([0, 0, 0], [0, -1, 0]), (2, [[0, 1, 0], [0, -1, 0]])],
        [Line([0, 0, 0], [0, 0, 1]), (2, [[0, 0, -1], [0, 0, 1]])],
        [Line([0, 0, 0], [0, 0, -1]), (2, [[0, 0, 1], [0, 0, -1]])],
        [Line([0, 0, 0], [1, 1, 1]), (2, [[-1, -1, -1], [1, 1, 1]])],
        [Line([0, 0, 0], [-1, -1, -1]), (2, [[1, 1, 1], [-1, -1, -1]])],
        [Line([0, 0, 0], [-1, 1, 1]), (2, [[1, -1, -1], [-1, 1, 1]])],
        [Line([0, 0, 0], [1, -1, -1]), (2, [[-1, 1, 1], [1, -1, -1]])],
        [Line([1, 0, 0], [1, 0, 1]), (2, [[1, 0, -1], [1, 0, 1]])],
        [Line([0, -1, 0], [-1, -1, 0]), (2, [[1, -1, 0], [-1, -1, 0]])],
        [Line([-1, -1, -1], [-1, 1, 1]), (2, [[-1, -1, -1], [-1, 1, 1]])],
        [Line([-1, -1, 1], [-1, 1, 1]), (2, [[-1, -1, 1], [-1, 1, 1]])],
        [Line([2, 0, 0], [1, 0, 1]), (1, [[1, 0, 1], [1, 0, 1]])],
        [Line([2, 0, 0], [1, 1, 1]), (1, [[1, 1, 1], [1, 1, 1]])],
        [Line([2, 0, 0], [2, 0, 1]), (0, [])],
    ],
)
def test_intersections_line_aabb_local_known(line, known):
    box = Box(2, 2, 2)
    count, points = intersections_line_aabb(line, box)
    assert count == known[0]
    assert count > 0 if len(points) > 0 else count == 0
    for i in range(count):
        assert points[i] == known[1][i]


def test_intersections_line_aabb_local_random():
    line = Line.from_point_direction_length([0, 0, 0], [0, 0, 1], 10)
    box = Box()

    for i in range(100):
        angles = random() * 2 * pi, random() * pi, random() * 2 * pi
        R = Rotation.from_euler_angles(angles)
        count, points = intersections_line_aabb(line.transformed(R), box)
        assert count == 2
        assert points[0] != points[1]
