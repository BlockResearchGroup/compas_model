from compas.geometry import Box
from compas.geometry import Point


def closestpoint_point_box(point: Point, box: Box) -> Point:
    """Compute the closest point from a point to a box.

    Parameters
    ----------
    point
        The source point.
    box
        The target box.

    Returns
    -------
    Point
        The closest point on the box.

    """
    pointvector = point - box.frame.point
    closest = Point(*box.frame.point)
    axes = box.frame.axes()
    extents = 0.5 * box.xsize, 0.5 * box.ysize, 0.5 * box.zsize
    for i in range(3):
        d = pointvector.dot(axes[i])
        d = max(min(d, extents[i]), -extents[i])
        closest += axes[i] * d
    return closest


def distance_point_box(point: Point, box: Box) -> float:
    """Compute the distance between a point and a box.

    Parameters
    ----------
    point
        The source point.
    box
        The target box.

    Returns
    -------
    float
        The distance between the point and the box.

    """
    closest = closestpoint_point_box(point, box)
    return point.distance_to_point(closest)
