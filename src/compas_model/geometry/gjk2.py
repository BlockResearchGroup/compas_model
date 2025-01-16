from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry import dot_vectors


def triplecross(u: Vector, v: Vector) -> Vector:
    """Compute the vector perpendicular to u in the plane uxv and in the same directio as v.

        Parameters
    ----------
    u : :class:`compas.geometry.Vector`
        The first vector.
    v : :class:`compas.geometry.Vector`
        The second vector.

    Returns
    -------
    :class:`compas.geometry.Vector`

    """
    return u.cross(v).cross(u)


# =============================================================================
# Support functions
# =============================================================================


def support_poly(points: list[Point], direction: Vector) -> Point:
    """Find the point in a list of points that is farthest away from the origin in a given direction.

    Parameters
    ----------
    points : list[:class:`compas.geometry.Point`]
        A list of points.

    Returns
    -------
    :class:`compas.geometry.Point`

    """
    point = points[0]
    maxdot = dot_vectors(point, direction)

    for p in points[1:]:
        d = dot_vectors(p, direction)
        if d > maxdot:
            maxdot = d
            point = p

    return point


def support_poly_poly(A: list[Vector], B: list[Vector], direction: Vector) -> Vector:
    """Compute a support point on the Minkowski sum of A and -B in the given direction.

    Parameters
    ----------
    A : list[:class:`compas.geometry.Vector`]
        Shape A represented by a list of point vectors.
    B : list[:class:`compas.geometry.Vector`]
        Shape B represented by a list of point vectors.
    direction : :class:`compas.geometry.Vector`
        The support direction.

    Returns
    -------
    :class:`compas.geometry.Vector`

    """
    return support_poly(A, direction) - support_poly(B, direction * -1)


# =============================================================================
# Simplex check
# =============================================================================


def do_simplex(simplex: list[Point], direction: Vector) -> bool:
    s = len(simplex)

    if s < 2:
        raise ValueError(f"The simplex should have at least two components (points): {s}")

    if s == 2:
        b = simplex[0]
        a = simplex[1]
        ao = a * -1
        ab = b - a

        if ab.dot(ao) >= 0:
            cross = triplecross(ab, ao)
            direction[0] = cross[0]
            direction[1] = cross[1]
        else:
            simplex.pop(0)
            direction[0] = ao[0]
            direction[1] = ao[1]

    else:
        # the simplex is a triangle
        # we should check if the triangle is valid
        # and if it contains the origin
        # otherwise we should return the line (or point) closest to the origin

        # check voronoi regions

        c = simplex[0]
        b = simplex[1]
        a = simplex[2]

        ao = a * -1
        ab = b - a
        ac = c - a

        if ab.dot(ao) >= 0:
            # ab in same direction as ao

            cross = triplecross(ab, ao)  # perpendicular to ab in direction of origin

            if ac.dot(cross) >= 0:
                # ac in same direction as perp to ab

                cross = triplecross(ac, ao)  # perpendicular to ac in direction of origin
                if ab.dot(cross) >= 0:
                    # origin is inside a, b, c
                    return True

                # remove b => edge closest to origin is ac
                # new direction is perpendicular to ac in direction of origin
                simplex.pop(1)
                direction[0] = cross[0]
                direction[1] = cross[1]

            else:
                # remove c => edge closest to origin is ab
                # new direction is perpendicular to ab in direction of origin
                simplex.pop(0)
                direction[0] = cross[0]
                direction[1] = cross[1]

        elif ac.dot(ao) >= 0:
            # ac in same direction as ao

            cross = triplecross(ac, ao)  # perpendicular to ac in direction of origin

            if ab.dot(cross) >= 0:
                # origin is inside a, b, c
                return True

            # remove b => edge closest to origin is ac
            # new direction is perpendicular to ac in direction of origin
            simplex.pop(1)
            direction[0] = cross[0]
            direction[1] = cross[1]

        else:
            # remove b and c => a is closest to origin
            # new direction is ao
            simplex.pop(1)
            simplex.pop(0)
            direction[0] = ao[0]
            direction[1] = ao[1]

    return False


# =============================================================================
# Collision checks
# =============================================================================


def is_collision_poly_poly_xy(A: Polygon, B: Polygon) -> bool:
    """Determine whether two convex polygons collide in the XY plane using the GJK algorithm.

    Parameters
    ----------
    A : :class:`compas.geometry.Polygon`
        The first polygon.
    B : :class:`compas.geometry.Polygon`
        The second polygon.

    Returns
    -------
    bool
        True if the polygons collide.
        False otherwise.

    Raises
    ------
    RuntimeError
        If the GJK algorithm doesn't converge after 100 iterations.

    Warnings
    --------
    Only works for convex polygons in the XY plane.

    Examples
    --------
    >>> from compas.geometry import Polygon
    >>> from compas_model.geometry import is_collision_poly_poly_xy

    Construct two polygons in the XY plane.

    >>> A = Polygon.from_rectangle([0, 0, 0], 2, 1)
    >>> B = Polygon.from_rectangle([1.5, 0.5, 0], 1, 1)

    Check if the polygons collide.

    >>> is_collision_poly_poly_xy(A, B)
    True

    """
    direction = [1, 0, 0]
    point = support_poly_poly(A, B, direction)
    simplex = [point]
    direction = point * -1

    for _ in range(100):
        # this should converge quite quickly

        point = support_poly_poly(A, B, direction)

        if point.dot(direction) < 0:
            return False

        simplex.append(point)  # minimum size is 2

        if do_simplex(simplex, direction):
            return True

    raise RuntimeError("GJK algorithm cannot terminate.")


# =============================================================================
# Distances
# =============================================================================
