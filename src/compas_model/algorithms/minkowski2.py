from math import atan2

from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry import centroid_points

# =============================================================================
# Helpers
# =============================================================================


def det(u: Vector, v: Vector) -> float:
    """Compute the determinant of the 2x2 matrix formed by the XY components of the vectors u and v.

    Parameters
    ----------
    u : :class:`compas.geometry.Vector`
        The first vector.
    v : :class:`compas.geometry.Vector`
        The second vector.

    Returns
    -------
    float

    """
    return u[0] * v[1] - u[1] * v[0]


def bottomleft(points: list[Point]) -> int:
    """Identify the point with the smalles y coordinate, and the smallest x coordinate.

    Parameters
    ----------
    points : list[:class:`compas.geometry.Point`]
        A list of points.

    Returns
    -------
    int
        The index of the point.

    """
    return sorted(enumerate(points), key=lambda x: (x[1][1], x[1][0]))[0][0]


def sort_ccw(points: list[Point]) -> list[Point]:
    """Sort the points in CCW direction using the polar angle wrt their centroid.

    Parameters
    ----------
    points : list[:class:`compas.geometry.Point`]
        A list of points.

    Returns
    -------
    list[:class:`compas.geometry.Point`]
        The sorted points.

    """
    cx, cy, _ = centroid_points(points)
    indices, points = zip(*sorted(enumerate(points), key=lambda x: atan2(x[1][1] - cy, x[1][0] - cx)))
    return [points[i] for i in indices]


def reorder_bottomleft(points: list[Point]) -> list[Point]:
    """Reorder the points to start with the one on the bottom left.

    Parameters
    ----------
    points : list[:class:`compas.geometry.Point`]
        A list of points.

    Returns
    -------
    list[:class:`compas.geometry.Point`]
        The reordered points.

    """
    index = bottomleft(points)
    return points[index:] + points[:index]


# =============================================================================
# Minkowski
# =============================================================================


def minkowski_sum_xy(A: Polygon, B: Polygon) -> Polygon:
    """Compute the Minkowski sum of two polygons.

    Parameters
    ----------
    A : :class:`compas.geometry.Polygon`
        The first polygon.
    B : :class:`compas.geometry.Polygon`
        The second polygon.

    Returns
    -------
    :class:`compas.geometry.Polygon`
        The polygon representing the sum.

    Warnings
    --------
    Currently only convex polygons are supported.

    See Also
    --------
    minkdiff2

    Notes
    -----
    ...

    References
    ----------
    ...

    """
    points = []

    A = reorder_bottomleft(sort_ccw(A))
    B = reorder_bottomleft(sort_ccw(B))

    i, j = 0, 0
    la, lb = len(A), len(B)

    while i < la or j < lb:
        points.append(A[i % la] + B[j % lb])
        d = det(A[(i + 1) % la] - A[i % la], B[(j + 1) % lb] - B[j % lb])
        if d >= 0:
            i += 1
        if d <= 0:
            j += 1

    return Polygon(points)


def minkowski_difference_xy(A: Polygon, B: Polygon) -> Polygon:
    """Compute the Minkowski sum of polygon A and inverted polygon B.

    Parameters
    ----------
    A : :class:`compas.geometry.Polygon`
        The first polygon.
    B : :class:`compas.geometry.Polygon`
        The second polygon.

    Returns
    -------
    :class:`compas.geometry.Polygon`
        The polygon representing the difference as the sum of A and -B.

    Warnings
    --------
    Currently only convex polygons are supported.

    See Also
    --------
    minksum2

    Notes
    -----
    ...

    References
    ----------
    ...

    """
    return minkowski_sum_xy(A, [Point(-x, -y, -z) for x, y, z in B])
