from math import inf
from typing import Union

from compas.geometry import Box
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Sphere
from compas.geometry import Vector
from compas.geometry import length_vector_sqrd
from compas.tolerance import TOL

# =============================================================================
# Intersection queries - Helpers
# =============================================================================


def is_line_contained_locally(point: Point, direction: Vector, dx: float, dy: float, dz: float) -> bool:
    """Determine whether the direction vector from a specific point is contained within the specified coordinate extents.

    Parameters
    ----------
    point : :class:`compas.geometry.Point`
        The base point of the direction.
    direction : :class:`compas.geometry.Vector`
        The direction vector.
    dx : float
        Extent of X coordinate.
    dy : float
        Extent of Y coordinate.
    dz : float
        Extent of Z coordinate.

    Returns
    -------
    bool
        True if the direction is contained.
        False otherwise.

    """
    dxp = direction.cross(point)

    dirx = abs(direction.x)
    diry = abs(direction.y)
    dirz = abs(direction.z)

    if abs(dxp.x) > dy * dirz + dz * diry:
        return False

    if abs(dxp.y) > dx * dirz + dz * dirx:
        return False

    if abs(dxp.z) > dx * diry + dy * dirx:
        return False

    return True


def is_ray_contained_locally(point: Point, direction: Vector, extents: list[float]) -> bool:
    """Determine whether a ray is contained within the given extents along local axes.

    Parameters
    ----------
    point : :class:`compas.geometry.Point`
        The base point of the ray.
    direction : :class:`compas.geometry.Vector`
        The direction of the ray.
    extents : list[float]
        The coordinate extents along local axes.

    Returns
    -------
    bool
        True if the ray is contained.
        False otherwise.

    """
    for i in range(3):
        if abs(point[i]) > extents[i] and point[i] * direction[i] >= 0:
            return False

    return is_line_contained_locally(point, direction, *extents)


def is_segment_contained_locally(point: Point, direction: Vector, box_extents: list[float], segment_extent: float) -> bool:
    """Determine whether a segment is contained within the given extents along local axes.

    Parameters
    ----------
    point : :class:`compas.geometry.Point`
        The midpoint of the segment.
    direction : :class:`compas.geometry.Vector`
        The direction of the segment.
    box_extents : list[float]
        The coordinate extents of the box along local axes.
    segment_extent : float
        Coordinate extent of the segment along its direction, wrt its midpoint.

    Returns
    -------
    bool
        True if the segment is contained.
        False otherwise.

    """
    for i in range(3):
        if abs(point[i]) > box_extents[i] + segment_extent * abs(direction[i]):
            return False

    return is_line_contained_locally(point, direction, *box_extents)


# =============================================================================
# Intersection queries
# =============================================================================


def is_intersection_line_box(line: Line, box: Box) -> bool:
    """Determine whether a line intersects an oriented box.

    Parameters
    ----------
    line : :class:`compas.geometry.Line`
        The line.
    box : :class:`compas.geometry.Box`
        The box.

    Returns
    -------
    bool
        True if the line intersects the box.
        False otherwise.

    """
    dx = 0.5 * box.xsize
    dy = 0.5 * box.ysize
    dz = 0.5 * box.zsize

    pointvector = line.point - box.frame.point
    direction = line.direction

    pointvector = Vector(
        pointvector.dot(box.frame.xaxis),
        pointvector.dot(box.frame.yaxis),
        pointvector.dot(box.frame.zaxis),
    )
    direction = Vector(
        direction.dot(box.frame.xaxis),
        direction.dot(box.frame.yaxis),
        direction.dot(box.frame.zaxis),
    )

    return is_line_contained_locally(pointvector, direction, dx, dy, dz)


def is_intersection_line_aabb(line: Line, box: Box) -> bool:
    """Determine whether a line intersects with an aligned box.

    Parameters
    ----------
    line : :class:`compas.geometry.Line`
        The line.
    box : :class:`compas.geometry.Box`
        The test box.

    Returns
    -------
    bool

    """
    dx = 0.5 * box.xsize
    dy = 0.5 * box.ysize
    dz = 0.5 * box.zsize

    pointvector = line.start - box.frame.point
    direction = line.direction

    return is_line_contained_locally(pointvector, direction, dx, dy, dz)


def is_intersection_ray_box(ray: Line, box: Box) -> bool:
    """Determine whether a ray intersects a box.

    Parameters
    ----------
    ray : :class:`compas.geometry.Line`
        The ray.
    box : :class:`compas.geometry.Box`
        The box.

    Returns
    -------
    bool
        True if the ray intersects the box.
        False otherwise.

    """
    pointvector = ray.point - box.frame.point
    direction = ray.direction
    extents = [0.5 * box.xsize, 0.5 * box.ysize, 0.5 * box.zsize]

    pointvector = Vector(
        pointvector.dot(box.frame.xaxis),
        pointvector.dot(box.frame.yaxis),
        pointvector.dot(box.frame.zaxis),
    )
    direction = Vector(
        direction.dot(box.frame.xaxis),
        direction.dot(box.frame.yaxis),
        direction.dot(box.frame.zaxis),
    )

    return is_ray_contained_locally(pointvector, direction, extents)


def is_intersection_ray_aabb(ray: Line, box: Box) -> bool:
    """Determine whether a ray intersects an axis aligned box.

    Parameters
    ----------
    ray : :class:`compas.geometry.Line`
        The ray.
    box : :class:`compas.geometry.Box`
        The box.

    Returns
    -------
    bool
        True if the ray intersects the box.
        False otherwise.

    """
    pointvector = ray.point - box.frame.point
    direction = ray.direction
    extents = [0.5 * box.xsize, 0.5 * box.ysize, 0.5 * box.zsize]

    return is_ray_contained_locally(pointvector, direction, extents)


def is_intersection_segment_box(segment: Line, box: Box) -> bool:
    """Determine whether a segment intersects a box.

    Parameters
    ----------
    segment : :class:`compas.geometry.Line`
        The segment.
    box : :class:`compas.geometry.Box`
        The box.

    Returns
    -------
    bool
        True if the segment intersects the box.
        False otherwise.

    """
    pointvector = segment.midpoint - box.frame.point
    direction = segment.direction

    segment_extent = 0.5 * segment.length
    box_extents = [0.5 * box.xsize, 0.5 * box.ysize, 0.5 * box.zsize]

    pointvector = Vector(
        pointvector.dot(box.frame.xaxis),
        pointvector.dot(box.frame.yaxis),
        pointvector.dot(box.frame.zaxis),
    )
    direction = Vector(
        direction.dot(box.frame.xaxis),
        direction.dot(box.frame.yaxis),
        direction.dot(box.frame.zaxis),
    )

    return is_segment_contained_locally(pointvector, direction, box_extents=box_extents, segment_extent=segment_extent)


def is_intersection_segment_aabb(segment: Line, box: Box) -> bool:
    """Determine whether a segment intersects an axis aligned box.

    Parameters
    ----------
    segment : :class:`compas.geometry.Line`
        The segment.
    box : :class:`compas.geometry.Box`
        The box.

    Returns
    -------
    bool
        True if the segmnet intersects the box.
        False otherwise.

    Warnings
    --------
    The name of this function can be misleading,
    since it returns `True` not only when the segment intersects the box boundary,
    but also when the segment is contained inside the box.

    This makes sense if you think of the box as a "solid", but is less intuitive when you think of it as a "shell".

    See Also
    --------
    is_intersection_segment_box

    Examples
    --------
    Note that :class:`Line` can be used as an infinite line, a rays, and as a segment between the two points at `t=0` and `t=1`.

    >>> from compas.geometry import Line
    >>> from compas.geometry import Box
    >>> from compas_model.geometry import is_intersection_segment_aabb

    Create a box centered at the origin.

    >>> box = Box(1, 1, 1)

    A segment crossing the box boundary intersects the box.

    >>> line = Line([0, 0, 0], [1, 0, 0])
    >>> is_intersection_segment_aabb(line, box)
    True

    A segment contained inside the box interiro intersects the box.

    >>> line = Line([0, 0, 0], [0.1, 0, 0])
    >>> is_intersection_segment_aabb(line, box)
    True

    A segment outside the box but with one point on the box boundary intersects the box.

    >>> line = Line([0.5, 0, 0], [1.5, 0, 0])
    >>> is_intersection_segment_aabb(line, box)
    True

    A segment outside the box doesn't intersect the box.

    >>> line = Line([1.0, 0, 0], [2.0, 0, 0])
    >>> is_intersection_segment_aabb(line, box)
    False

    """
    pointvector = segment.midpoint - box.frame.point
    direction = segment.direction

    segment_extent = 0.5 * segment.length
    box_extents = [0.5 * box.xsize, 0.5 * box.ysize, 0.5 * box.zsize]

    return is_segment_contained_locally(pointvector, direction, box_extents=box_extents, segment_extent=segment_extent)


def is_intersection_box_box(a: Box, b: Box) -> bool:
    """Determine whether a box intersects another box.

    Parameters
    ----------
    a : :class:`compas.geometry.Box`
        The first box.
    b : :class:`compas.geometry.Box`
        The second box.

    Returns
    -------
    bool
        True if the boxes intersect.
        False otherwise.

    Notes
    -----
    The algorithm uses the method of separating axes, which states, for two convex objects:
    If there exists a line for which the intervals of projection of the two objects onto that line do not intersect,
    then the objects do not intersect.

    The underlying theorem is described here [1]_.

    For two oriented (bounding) boxes, this can be formulated in the form of 15 axis checks,
    based on the coordinate frames of the boxes, and the box coordinate extents.

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Hyperplane_separation_theorem

    Examples
    --------
    >>> from compas.geometry import Box, Frame
    >>> from compas_model.geometry import is_intersection_box_box

    >>> A = Box(2, 2, 2)
    >>> B = Box(1, 1, 1, frame=Frame(point=[1, 1, 1], xaxis=[1, 1, 0], yaxis=[-1, 1, 0]))

    >>> is_intersection_box_box(A, B)
    True

    """
    da = [0.5 * a.xsize, 0.5 * a.ysize, 0.5 * a.zsize]
    db = [0.5 * b.xsize, 0.5 * b.ysize, 0.5 * b.zsize]

    center = b.frame.point - a.frame.point

    C = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    absC = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    # a.xaxis
    C[0][0] = a.frame.xaxis.dot(b.frame.xaxis)
    C[0][1] = a.frame.xaxis.dot(b.frame.yaxis)
    C[0][2] = a.frame.xaxis.dot(b.frame.zaxis)

    absC[0][0] = abs(C[0][0])
    absC[0][1] = abs(C[0][1])
    absC[0][2] = abs(C[0][2])

    if abs(a.frame.xaxis.dot(center)) > da[0] + db[0] * absC[0][0] + db[1] * absC[0][1] + db[2] * absC[0][2]:
        return False

    # a.yaxis
    C[1][0] = a.frame.yaxis.dot(b.frame.xaxis)
    C[1][1] = a.frame.yaxis.dot(b.frame.yaxis)
    C[1][2] = a.frame.yaxis.dot(b.frame.zaxis)

    absC[1][0] = abs(C[1][0])
    absC[1][1] = abs(C[1][1])
    absC[1][2] = abs(C[1][2])

    if abs(a.frame.yaxis.dot(center)) > da[1] + db[0] * absC[1][0] + db[1] * absC[1][1] + db[2] * absC[1][2]:
        return False

    # a.zaxis
    C[2][0] = a.frame.zaxis.dot(b.frame.xaxis)
    C[2][1] = a.frame.zaxis.dot(b.frame.yaxis)
    C[2][2] = a.frame.zaxis.dot(b.frame.zaxis)

    absC[2][0] = abs(C[2][0])
    absC[2][1] = abs(C[2][1])
    absC[2][2] = abs(C[2][2])

    if abs(a.frame.zaxis.dot(center)) > da[2] + db[0] * absC[2][0] + db[1] * absC[2][1] + db[2] * absC[2][2]:
        return False

    # b.xaxis
    if abs(b.frame.xaxis.dot(center)) > da[0] * absC[0][0] + da[1] * absC[0][1] + da[2] * absC[0][2] + db[0]:
        return False

    # b.yaxis
    if abs(b.frame.yaxis.dot(center)) > da[0] * absC[1][0] + da[1] * absC[1][1] + da[2] * absC[1][2] + db[1]:
        return False

    # b.zaxis
    if abs(b.frame.zaxis.dot(center)) > da[0] * absC[2][0] + da[1] * absC[2][1] + da[2] * absC[2][2] + db[2]:
        return False

    ax_b = [a.frame.zaxis.dot(center), a.frame.yaxis.dot(center)]

    # a.xaxis.cross(b.xaxis)
    if abs(C[1][0] * ax_b[0] - C[2][0] * ax_b[1]) > da[1] * absC[2][0] + da[2] * absC[1][0] + db[1] * absC[0][2] + db[2] * absC[0][1]:
        return False

    # a.xaxis.cross(b.yaxis)
    if abs(C[1][1] * ax_b[0] - C[2][1] * ax_b[1]) > da[1] * absC[2][1] + da[2] * absC[1][1] + db[0] * absC[0][2] + db[2] * absC[0][0]:
        return False

    # a.xaxis.cross(b.zaxis)
    if abs(C[1][2] * ax_b[0] - C[2][2] * ax_b[1]) > da[1] * absC[2][2] + da[2] * absC[1][2] + db[0] * absC[0][1] + db[1] * absC[0][0]:
        return False

    ay_b = [a.frame.xaxis.dot(center), a.frame.zaxis.dot(center)]

    # a.yaxis.cross(b.xaxis)
    if abs(C[2][0] * ay_b[0] - C[0][0] * ay_b[1]) > da[0] * absC[2][0] + da[2] * absC[0][0] + db[1] * absC[1][2] + db[2] * absC[1][1]:
        return False

    # a.yaxis.cross(b.yaxis)
    if abs(C[2][1] * ay_b[0] - C[0][1] * ay_b[1]) > da[0] * absC[2][1] + da[2] * absC[0][1] + db[0] * absC[1][2] + db[2] * absC[1][0]:
        return False

    # a.yaxis.cross(b.zaxis)
    if abs(C[2][2] * ay_b[0] - C[0][2] * ay_b[1]) > da[0] * absC[2][2] + da[2] * absC[0][2] + db[0] * absC[1][1] + db[1] * absC[1][0]:
        return False

    az_b = [a.frame.yaxis.dot(center), a.frame.xaxis.dot(center)]

    # a.zaxis.cross(b.xaxis)
    if abs(C[0][0] * az_b[0] - C[1][0] * az_b[1]) > da[0] * absC[1][0] + da[1] * absC[0][0] + db[1] * absC[2][2] + db[2] * absC[2][1]:
        return False

    # a.zaxis.cross(b.yaxis)
    if abs(C[0][1] * az_b[0] - C[1][1] * az_b[1]) > da[0] * absC[1][1] + da[1] * absC[0][1] + db[0] * absC[2][2] + db[2] * absC[2][0]:
        return False

    # a.zaxis.cross(b.zaxis)
    if abs(C[0][2] * az_b[0] - C[1][2] * az_b[1]) > da[0] * absC[1][2] + da[1] * absC[0][2] + db[0] * absC[2][1] + db[1] * absC[2][0]:
        return False

    return True


# def is_intersection_aabb_aabb(a: Box, b: Box) -> bool:
#     """Determine whether two axis aligned boxes intersect.

#     Parameters
#     ----------
#     a : :class:`compas.geometry.Box`
#         The first box.
#     b : :class:`compas.geometry.Box`
#         The second box.

#     Returns
#     -------
#     bool
#         True if the boxes intersect.
#         False otherwise.

#     """
#     pass


def is_intersection_sphere_box(sphere: Sphere, box: Box) -> bool:
    """Determine whether a sphere intersects an oriented box.

    Parameters
    ----------
    sphere : :class:`compas.geometry.Sphere`
        The sphere.
    box : :class:`compas.geometry.Box`
        The box.

    Returns
    -------
    bool
        True if the sphere intersects the box.
        False otherwise.

    """
    point = sphere.frame.point
    direction = box.frame.point - sphere.frame.point

    if length_vector_sqrd(direction) < sphere.radius**2:
        return True

    direction.unitize()
    segment = Line.from_point_direction_length(point, direction, sphere.radius)
    return is_intersection_segment_box(segment, box)


def is_intersection_sphere_aabb(sphere: Sphere, box: Box) -> bool:
    """Determine whether a sphere intersects an axis-aligned box.

    Parameters
    ----------
    sphere : :class:`compas.geometry.Sphere`
        The sphere.
    box : :class:`compas.geometry.Box`
        The box.

    Returns
    -------
    bool
        True if the sphere intersects the aabb.
        False otherwise.

    """
    point = sphere.frame.point
    direction = box.frame.point - sphere.frame.point

    if length_vector_sqrd(direction) < sphere.radius**2:
        return True

    direction.unitize()
    segment = Line.from_point_direction_length(point, direction, sphere.radius)
    return is_intersection_segment_aabb(segment, box)


# =============================================================================
# Intersection points - Helpers
# =============================================================================


def is_clipped(denominator: float, numerator: float, t: list[float]) -> bool:
    if denominator > 0:
        if numerator > denominator * t[1]:
            return False
        if numerator > denominator * t[0]:
            t[0] = numerator / denominator
        return True
    if denominator < 0:
        if numerator > denominator * t[0]:
            return False
        if numerator > denominator * t[1]:
            t[1] = numerator / denominator
        return True
    return numerator <= 0


def intersections_line_box_locally(point: Point, direction: Vector, extents: list[float]) -> tuple[int, list[Point]]:
    t = [-inf, inf]
    dx, dy, dz = extents

    not_culled: bool = (
        is_clipped(+direction.x, -point.x - dx, t)
        and is_clipped(-direction.x, +point.x - dx, t)
        and is_clipped(+direction.y, -point.y - dy, t)
        and is_clipped(-direction.y, +point.y - dy, t)
        and is_clipped(+direction.z, -point.z - dz, t)
        and is_clipped(-direction.z, +point.z - dz, t)
    )

    count: int

    if not_culled:
        if t[1] > t[0]:
            count = 2
        else:
            count = 1
            t[1] = t[0]
    else:
        count = 0
        t = [inf, -inf]

    return count, t


def intersections_ray_box_locally(point: Point, direction: Vector, extents: list[float]) -> tuple[int, list[Point]]:
    count, t = intersections_line_box_locally(point, direction, extents)

    if count > 0:
        if t[1] >= 0:
            if t[0] < 0:
                t[0] = 0
        else:
            count = 0

    return count, t


# =============================================================================
# Intersection points
# =============================================================================


def intersection_ray_triangle(line: Line, triangle: list[Point]) -> Union[Point, None]:
    """Compute the intersection between a ray and a triangle.

    Parameters
    ----------
    line : :class:`compas.geometry.Line`
        The ray.
    triangle : list[:class:`compas.geometry.Point`]
        The triangle as a list of three points.

    Results
    -------
    :class:`compas.geometry.Point` | None
        The intersection point if one exists.

    Notes
    -----
    The function is an implementation of the Möller-Trumbore intersection algorithm [1]_.

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/M%C3%B6ller%E2%80%93Trumbore_intersection_algorithm

    """
    point = line.point
    direction = line.direction
    a, b, c = triangle
    ab = b - a
    ac = c - a
    d_ac = direction.cross(ac)

    det = ab.dot(d_ac)
    if TOL.is_zero(det):
        return

    inv_det = 1.0 / det
    ap = point - a

    u = inv_det * ap.dot(d_ac)
    if TOL.is_negative(u) or TOL.is_positive(u - 1):
        return

    ap_ab = ap.cross(ab)

    v = inv_det * direction.dot(ap_ab)
    if TOL.is_negative(v) or TOL.is_positive(u + v - 1):
        return

    t = inv_det * ac.dot(ap_ab)

    if TOL.is_positive(t):
        return point + direction * t

    return None


def intersections_line_box(line: Line, box: Box) -> tuple[int, list[Point]]:
    """Find the intersections between a line and a box.

    Parameters
    ----------
    line : :class:`compas.geometry.Line`
        The line.
    box : :class:`compas.geometry.Box`
        An oriented box.

    Returns
    -------
    tuple[bool, list[:class:`compas.geometry.Point`]]
        The number of intersections, and a list of intersection points.
        If the number of intersections is 0 (zero), the list is empty.
        If the number of intersections is 1 (one), the list contains two identical points.
        If the number of intersections is 2 (two), the list contains two distinct points.

    """
    pointvector = line.point - box.frame.point
    direction = line.direction
    extents = [0.5 * box.xsize, 0.5 * box.ysize, 0.5 * box.zsize]

    pointvector = Vector(
        pointvector.dot(box.frame.xaxis),
        pointvector.dot(box.frame.yaxis),
        pointvector.dot(box.frame.zaxis),
    )
    direction = Vector(
        direction.dot(box.frame.xaxis),
        direction.dot(box.frame.yaxis),
        direction.dot(box.frame.zaxis),
    )

    count, t = intersections_line_box_locally(pointvector, direction, extents)
    points = []

    if count:
        point = line.point
        direction = line.direction
        for i in range(count):
            points.append(point + direction * t[i])

    return count, points


def intersections_line_aabb(line: Line, box: Box) -> tuple[int, list[Point]]:
    """Find the intersections between a line and an axis aligned box.

    Parameters
    ----------
    line : :class:`compas.geometry.Line`
        The line.
    box : :class:`compas.geometry.Box`
        An axis aligned box.

    Returns
    -------
    tuple[bool, list[:class:`compas.geometry.Point`]]
        The number of intersections, and a list of intersection points.
        If the number of intersections is 0 (zero), the list is empty.
        If the number of intersections is 1 (one), the list contains two identical points.
        If the number of intersections is 2 (two), the list contains two distinct points.

    """
    pointvector = line.point - box.frame.point
    direction = line.direction
    extents = [0.5 * box.xsize, 0.5 * box.ysize, 0.5 * box.zsize]

    count, t = intersections_line_box_locally(pointvector, direction, extents)
    points = []

    if count:
        point = line.point
        direction = line.direction
        for i in range(count):
            points.append(point + direction * t[i])

    return count, points


def intersections_ray_box(ray: Line, box: Box) -> tuple[int, list[Point]]:
    """Find the intersections between a ray and a box.

    Parameters
    ----------
    ray : :class:`compas.geometry.Line`
        The line.
    box : :class:`compas.geometry.Box`
        An oriented box.

    Returns
    -------
    tuple[bool, list[:class:`compas.geometry.Point`]]
        The number of intersections, and a list of intersection points.
        If the number of intersections is 0 (zero), the list is empty.
        If the number of intersections is 1 (one), the list contains two identical points.
        If the number of intersections is 2 (two), the list contains two distinct points.

    """
    pointvector = ray.point - box.frame.point
    direction = ray.direction
    extents = [0.5 * box.xsize, 0.5 * box.ysize, 0.5 * box.zsize]

    pointvector = Vector(
        pointvector.dot(box.frame.xaxis),
        pointvector.dot(box.frame.yaxis),
        pointvector.dot(box.frame.zaxis),
    )
    direction = Vector(
        direction.dot(box.frame.xaxis),
        direction.dot(box.frame.yaxis),
        direction.dot(box.frame.zaxis),
    )

    count, t = intersections_ray_box_locally(pointvector, direction, extents)
    points = []

    if count:
        point = ray.point
        direction = ray.direction
        for i in range(count):
            points.append(point + direction * t[i])

    return count, points


def intersections_ray_aabb(ray: Line, box: Box) -> tuple[int, list[Point]]:
    """Find the intersections between a ray and an axis aligned box.

    Parameters
    ----------
    ray : :class:`compas.geometry.Line`
        The ray.
    box : :class:`compas.geometry.Box`
        An axis aligned box.

    Returns
    -------
    tuple[bool, list[:class:`compas.geometry.Point`]]
        The number of intersections, and a list of intersection points.
        If the number of intersections is 0 (zero), the list is empty.
        If the number of intersections is 1 (one), the list contains two identical points.
        If the number of intersections is 2 (two), the list contains two distinct points.

    """
    pointvector = ray.point - box.frame.point
    direction = ray.direction
    extents = [0.5 * box.xsize, 0.5 * box.ysize, 0.5 * box.zsize]

    count, t = intersections_ray_box_locally(pointvector, direction, extents)
    points = []

    if count:
        point = ray.point
        direction = ray.direction
        for i in range(count):
            points.append(point + direction * t[i])

    return count, points


# def intersections_segment_box():
#     pass


# def intersections_segment_aabb():
#     pass
