from math import atan2

from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry import centroid_points_xy
from compas.geometry import distance_point_line_sqrd_xy
from compas.geometry import dot_vectors_xy
from compas.itertools import pairwise


def cross(u: Vector, v: Vector) -> float:
    return u[0] * v[1] - u[1] * v[0]


def bottomleft(points) -> int:
    return sorted(enumerate(points), key=lambda x: (x[1][1], x[1][0]))[0][0]


def sort_ccw(points: list[Point]):
    cx, cy, cz = centroid_points_xy(points)
    indices, points = zip(*sorted(enumerate(points), key=lambda x: atan2(x[1][1] - cy, x[1][0] - cx)))
    return [points[i] for i in indices]


def sort_bottomleft(points: list[Point]) -> list[Point]:
    index = bottomleft(points)
    return points[index:] + points[:index]


def support_point(A: list[Vector], direction: Vector) -> Vector:
    return sorted(A, key=lambda point: dot_vectors_xy(point, direction))[-1]


def support(A: list[Vector], B: list[Vector], direction: Vector) -> Vector:
    return support_point(A, direction) - support_point(B, direction * -1)


def closest_edge_to_origin(abc) -> tuple[Point, Point]:
    return sorted(pairwise(abc + abc[:1]), key=lambda line: distance_point_line_sqrd_xy([0, 0, 0], line))[0]


def minksum2(A: Polygon, B: Polygon) -> Polygon:
    points = []

    A = sort_bottomleft(sort_ccw(A))
    B = sort_bottomleft(sort_ccw(B))

    i, j = 0, 0
    la, lb = len(A), len(B)

    while i < la or j < lb:
        points.append(A[i % la] + B[j % lb])
        d = cross(A[(i + 1) % la] - A[i % la], B[(j + 1) % lb] - B[j % lb])
        if d >= 0:
            i += 1
        if d <= 0:
            j += 1

    return Polygon(points)


def minkdiff2(A: Polygon, B: Polygon) -> Polygon:
    return minksum2(A, [Point(-x, -y, -z) for x, y, z in B])
