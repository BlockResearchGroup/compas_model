from compas.geometry import Box
from compas.geometry import Point


def closestpoint_point_box(point: Point, box: Box) -> Point:
    """Compute the closest point to a box from another point.

    Parameters
    ----------
    point : :class:`compas.geometry.Point`
        The point.
    box : :class:`compas.geometry.Box`
        The box.

    Returns
    -------
    :class:`compas.geometry.Point`

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
    closest = closestpoint_point_box(point, box)
    return point.distance_to_point(closest)
