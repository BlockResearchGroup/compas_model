from math import pi
import pytest
from pytest import mark
from random import random

from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Rotation
from compas.geometry import Sphere
from compas.geometry import Translation
from compas_model.geometry import intersection_ray_triangle
from compas_model.geometry import intersections_line_aabb
from compas_model.geometry import intersections_line_box
from compas_model.geometry import intersections_ray_aabb
from compas_model.geometry import intersections_ray_box
from compas_model.geometry import is_intersection_aabb_aabb
from compas_model.geometry import is_intersection_box_box
from compas_model.geometry import is_intersection_line_aabb
from compas_model.geometry import is_intersection_line_box
from compas_model.geometry import is_intersection_ray_aabb
from compas_model.geometry import is_intersection_ray_box
from compas_model.geometry import is_intersection_segment_aabb
from compas_model.geometry import is_intersection_segment_box
from compas_model.geometry import is_intersection_sphere_aabb
from compas_model.geometry import is_intersection_sphere_box


def assert_points_equal(points, expected):
    assert len(points) == len(expected)
    assert all(point == coordinates for point, coordinates in zip(points, expected))


@mark.parametrize(
    ["line", "result"],
    [
        (Line([-2, 0, 0], [2, 0, 0]), True),
        (Line([-2, 0.5, 0], [2, 0.5, 0]), True),
        (Line([-2, 0.5, 0.5], [2, 0.5, 0.5]), True),
        (Line([-2, 0.5001, 0], [2, 0.5001, 0]), False),
        (Line([-2, 1, 0], [2, 1, 0]), False),
    ],
)
def test_is_intersection_line_aabb_boundary_cases(line, result):
    assert is_intersection_line_aabb(line, Box()) is result


def test_is_intersection_line_box_is_transformation_invariant():
    box = Box()
    line = Line([-2, 0.25, 0], [2, 0.25, 0])
    transformation = Translation.from_vector([3, -2, 5]) * Rotation.from_axis_and_angle([0, 0, 1], pi / 4)

    assert is_intersection_line_box(line, box)
    assert is_intersection_line_box(line.transformed(transformation), box.transformed(transformation))


@mark.parametrize(
    ["ray", "result"],
    [
        (Line([-2, 0, 0], [-3, 0, 0]), False),
        (Line([-2, 0, 0], [0, 0, 0]), True),
        (Line([0, 0, 0], [1, 0, 0]), True),
        (Line([0.5, 0, 0], [1.5, 0, 0]), True),
        (Line([0.5, 0.5, 0], [1.5, 0.5, 0]), True),
        (Line([-2, 0.5001, 0], [0, 0.5001, 0]), False),
    ],
)
def test_is_intersection_ray_aabb_boundary_cases(ray, result):
    assert is_intersection_ray_aabb(ray, Box()) is result


def test_is_intersection_ray_box_is_transformation_invariant():
    box = Box()
    ray = Line([-2, 0.25, 0], [0, 0.25, 0])
    transformation = Rotation.from_axis_and_angle([0, 1, 0], pi / 3)

    assert is_intersection_ray_box(ray, box)
    assert is_intersection_ray_box(ray.transformed(transformation), box.transformed(transformation))


@mark.parametrize(
    ["segment", "result"],
    [
        (Line([-2, 0, 0], [2, 0, 0]), True),
        (Line([-0.25, 0, 0], [0.25, 0, 0]), True),
        (Line([0.5, 0, 0], [1.5, 0, 0]), True),
        (Line([0.5, 0.5, 0.5], [1, 1, 1]), True),
        (Line([0.5001, 0, 0], [1.5, 0, 0]), False),
        (Line([1, 0, 0], [2, 0, 0]), False),
    ],
)
def test_is_intersection_segment_aabb_boundary_cases(segment, result):
    assert is_intersection_segment_aabb(segment, Box()) is result


def test_is_intersection_segment_box_is_transformation_invariant():
    box = Box()
    segment = Line([-1, 0.25, 0], [1, 0.25, 0])
    transformation = Translation.from_vector([1, 2, 3]) * Rotation.from_axis_and_angle([1, 0, 0], pi / 3)

    assert is_intersection_segment_box(segment, box)
    assert is_intersection_segment_box(segment.transformed(transformation), box.transformed(transformation))


@mark.parametrize(
    ["offset", "result"],
    [
        ([0, 0, 0], True),
        ([1, 0, 0], True),
        ([1, 1, 0], True),
        ([1, 1, 1], True),
        ([1.0001, 0, 0], False),
        ([0, 1.0001, 0], False),
        ([0, 0, 1.0001], False),
    ],
)
def test_is_intersection_box_box_boundary_cases(offset, result):
    a = Box()
    b = Box()
    b.translate(offset)

    assert is_intersection_box_box(a, b) is result
    assert is_intersection_box_box(b, a) is result


def test_is_intersection_box_box_oriented_separated_and_intersecting():
    a = Box()
    b = Box(frame=Frame([0.7, 0, 0], [1, 1, 0], [-1, 1, 0]))
    c = Box(frame=Frame([2, 0, 0], [1, 1, 0], [-1, 1, 0]))

    assert is_intersection_box_box(a, b)
    assert not is_intersection_box_box(a, c)


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
    ["point", "radius", "result"],
    [
        ([0, 0, 0], 0.1, True),
        ([1, 0, 0], 0.5, True),
        ([1, 0, 0], 0.4999, False),
        ([1, 1, 0], 2**0.5 / 2, True),
        ([1, 1, 0], 2**0.5 / 2 - 0.0001, False),
        ([1, 1, 1], 3**0.5 / 2, True),
        ([1, 1, 1], 3**0.5 / 2 - 0.0001, False),
    ],
)
def test_is_intersection_sphere_aabb_boundary_cases(point, radius, result):
    assert is_intersection_sphere_aabb(Sphere(point=point, radius=radius), Box()) is result


def test_is_intersection_sphere_box_is_transformation_invariant():
    box = Box()
    sphere = Sphere(point=[1, 0, 0], radius=0.5)
    transformation = Translation.from_vector([2, 3, 4]) * Rotation.from_axis_and_angle([0, 0, 1], pi / 4)

    assert is_intersection_sphere_box(sphere, box)
    assert is_intersection_sphere_box(sphere.transformed(transformation), box.transformed(transformation))


@mark.parametrize(
    ["offset", "tolerance", "include_touching", "result"],
    [
        ([0, 0, 0], 0.0, True, True),
        ([0.5, 0.5, 0.5], 0.0, True, True),
        ([1.0, 0, 0], 0.0, True, True),
        ([1.0, 0, 0], 0.0, False, False),
        ([1.0001, 0, 0], 0.0, True, False),
        ([1.0001, 0, 0], 0.001, True, True),
        ([0.9999, 0, 0], 0.001, False, False),
        ([0.998, 0, 0], 0.001, False, True),
        ([0, 1.1, 0], 0.0, True, False),
        ([0, 0, 1.1], 0.0, True, False),
    ],
)
def test_is_intersection_aabb_aabb(offset, tolerance, include_touching, result):
    a = Box(1, 1, 1)
    b = Box(1, 1, 1)
    b.translate(offset)

    assert is_intersection_aabb_aabb(a, b, tolerance=tolerance, include_touching=include_touching) is result


def test_is_intersection_aabb_aabb_rejects_negative_tolerance():
    with pytest.raises(ValueError):
        is_intersection_aabb_aabb(Box(), Box(), tolerance=-1e-6)


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


@mark.parametrize(
    ["ray", "count", "expected"],
    [
        (Line([-2, 0, 0], [0, 0, 0]), 2, [[-1, 0, 0], [1, 0, 0]]),
        (Line([-2, 0, 0], [-3, 0, 0]), 0, []),
        (Line([0, 0, 0], [1, 0, 0]), 2, [[0, 0, 0], [1, 0, 0]]),
        (Line([-1, 0, 0], [0, 0, 0]), 2, [[-1, 0, 0], [1, 0, 0]]),
        (Line([-2, 0, 0], [0, 2, 0]), 1, [[-1, 1, 0]]),
        (Line([-2, 1.0001, 0], [0, 1.0001, 0]), 0, []),
    ],
)
def test_intersections_ray_aabb_boundary_cases(ray, count, expected):
    actual_count, points = intersections_ray_aabb(ray, Box(2, 2, 2))

    assert actual_count == count
    assert_points_equal(points, expected)


def test_intersections_line_box_is_transformation_invariant():
    box = Box(2, 2, 2)
    line = Line([-2, 0, 0], [2, 0, 0])
    transformation = Translation.from_vector([3, 4, 5]) * Rotation.from_axis_and_angle([0, 0, 1], pi / 4)

    count, points = intersections_line_box(line.transformed(transformation), box.transformed(transformation))

    assert count == 2
    assert_points_equal(points, [Point(-1, 0, 0).transformed(transformation), Point(1, 0, 0).transformed(transformation)])


def test_intersections_ray_box_is_transformation_invariant():
    box = Box(2, 2, 2)
    ray = Line([-2, 0, 0], [0, 0, 0])
    transformation = Translation.from_vector([3, 4, 5]) * Rotation.from_axis_and_angle([0, 1, 0], pi / 4)

    count, points = intersections_ray_box(ray.transformed(transformation), box.transformed(transformation))

    assert count == 2
    assert_points_equal(points, [Point(-1, 0, 0).transformed(transformation), Point(1, 0, 0).transformed(transformation)])


@mark.parametrize(
    ["ray", "expected"],
    [
        (Line([0.25, 0.25, 1], [0.25, 0.25, -1]), [0.25, 0.25, 0]),
        (Line([0, 0, 1], [0, 0, -1]), [0, 0, 0]),
        (Line([0.5, 0.5, 1], [0.5, 0.5, -1]), [0.5, 0.5, 0]),
        (Line([0.5, 0, 1], [0.5, 0, -1]), [0.5, 0, 0]),
        (Line([0.5001, 0.5, 1], [0.5001, 0.5, -1]), None),
        (Line([0, 0, 1], [0, 0, 2]), None),
        (Line([0, 0, 0], [0, 0, 1]), None),
        (Line([0, 0, 1], [1, 0, 1]), None),
    ],
)
def test_intersection_ray_triangle_boundary_and_failure_cases(ray, expected):
    triangle = [Point(0, 0, 0), Point(1, 0, 0), Point(0, 1, 0)]

    result = intersection_ray_triangle(ray, triangle)

    if expected is None:
        assert result is None
    else:
        assert result == expected


def test_intersection_ray_triangle_degenerate_triangle_returns_none():
    triangle = [Point(0, 0, 0), Point(1, 0, 0), Point(2, 0, 0)]

    assert intersection_ray_triangle(Line([0.5, 0, 1], [0.5, 0, -1]), triangle) is None


@mark.parametrize("triangle", [[], [Point(0, 0, 0)], [Point(0, 0, 0), Point(1, 0, 0)], [Point(0, 0, 0)] * 4])
def test_intersection_ray_triangle_rejects_invalid_vertex_count(triangle):
    with pytest.raises(ValueError):
        intersection_ray_triangle(Line([0, 0, 1], [0, 0, -1]), triangle)
