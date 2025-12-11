from math import fabs
from typing import Optional
from typing import Type
from typing import Union

from shapely.geometry import Polygon as ShapelyPolygon

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Vector
from compas.geometry import bestfit_frame_numpy
from compas.geometry import centroid_polygon
from compas.geometry import cross_vectors
from compas.geometry import dot_vectors
from compas.geometry import length_vector
from compas.geometry import transform_points
from compas.tolerance import TOL
from compas.tolerance import Tolerance
from compas_model.interactions import Contact


def is_opposite_vector_vector(u: Union[Vector, list[float]], v: Union[Vector, list[float]], tol=None) -> bool:
    """Check if two vectors are opposite.

    Parameters
    ----------
    u : Vector | list[float]
        The first vector.
    v : Vector | list[float]
        The second vector.
    tol : float, optional
        Tolerance for the check.

    Returns
    -------
    bool

    Notes
    -----
    Two vectors are considered parallel if their cross product is zero.
    They are considered opposite if they are parallel and their dot product is -1.

    """
    return TOL.is_zero(length_vector(cross_vectors(u, v)), tol) and TOL.is_close(dot_vectors(u, v), -1, rtol=1e-3)


def is_opposite_normal_normal(u: Union[Vector, list[float]], v: Union[Vector, list[float]]) -> bool:
    """Check if two normals are opposite.

    Parameters
    ----------
    u : Vector | list[float]
        The first normal.
    v : Vector | list[float]
        The second normal.

    Returns
    -------
    bool

    Notes
    -----
    This function is similar to `is_opposite_vector_vector` but uses a relative tolerance for the dot product check.

    """
    return TOL.is_close(dot_vectors(u, v), -1, rtol=1e-3)


def mesh_mesh_contacts(
    a: Mesh,
    b: Mesh,
    tolerance: float = 1e-6,
    minimum_area: float = 1e-1,
    contacttype: Type[Contact] = Contact,
) -> list[Contact]:
    """Compute all face-face contact interfaces between two meshes.

    Parameters
    ----------
    a : Mesh
        The source mesh.
    b : Mesh
        The target mesh.
    tolerance : float, optional
        Maximum deviation from the perfectly flat interface plane.
    minimum_area : float, optional
        Minimum area of a "face-face" interface.

    Returns
    -------
    list[Contact]

    Notes
    -----
    For equilibrium calculations (e.g. with CRA), it is important that interface frames are aligned
    with the direction of the (interaction) edges on which they are stored.

    This means that if the bestfit frame does not align with the normal of the base source frame,
    it will be inverted, such that it corresponds to whatever edge is created from this source to a target.

    """
    # tolerance is used both for parallelity and for copenetration
    # perhaps two different thresholds should be used

    contacts: list[Contact] = []

    for a_face in a.faces():
        a_points = a.face_coordinates(a_face)
        a_normal = a.face_normal(a_face)

        for b_face in b.faces():
            b_points = b.face_coordinates(b_face)
            b_normal = b.face_normal(b_face)

            # normals should actually be exactly opposite
            # parallelity is not enough

            if not is_opposite_normal_normal(a_normal, b_normal):
                continue

            result = polygon_polygon_overlap(a_points, b_points, a_normal, tolerance, minimum_area)  # type: ignore

            # this is not always an accurate representation of the interface
            # if the polygon has holes
            # the interface is incorrect

            if result:
                points, frame, area, matrix_to_local, matrix_to_world = result
                contact = contacttype(points=points, frame=frame, size=area)
                contacts.append(contact)

    return contacts


def brep_brep_contacts(
    a: Brep,
    b: Brep,
    tolerance: float = 1e-6,
    minimum_area: float = 1e-1,
    deflection: Optional[float] = None,
    contacttype: Type[Contact] = Contact,
) -> list[Contact]:
    """Compute all face-face contact interfaces between two meshes.

    Parameters
    ----------
    a : Brep
        The source brep.
    b : Brep
        The target brep.
    tolerance : float, optional
        Maximum deviation from the perfectly flat interface plane.
    minimum_area : float, optional
        Minimum area of a "face-face" interface.

    Returns
    -------
    list[Contact]

    Notes
    -----
    For equilibrium calculations (e.g. with CRA), it is important that interface frames are aligned
    with the direction of the (interaction) edges on which they are stored.

    This means that if the bestfit frame does not align with the normal of the base source frame,
    it will be inverted, such that it corresponds to whatever edge is created from this source to a target.

    """
    contacts: list[Contact] = []

    deflection = deflection or Tolerance().lineardeflection

    # the parameter name linear_deflection is specific to OCC
    a_faces, b_faces = a.overlap(b, linear_deflection=deflection, tolerance=tolerance)  # type: ignore

    if a_faces and b_faces:
        for a_face in a_faces:
            if a_face.area < minimum_area:
                continue

            a_poly: Polygon = a_face.to_polygon()
            a_points = a_poly.points
            a_normal = a_poly.normal.unitized()

            for b_face in b_faces:
                if b_face.area < minimum_area:
                    continue

                b_poly: Polygon = b_face.to_polygon()
                b_points = b_poly.points
                b_normal = b_poly.normal.unitized()

                # normals should actually be exactly opposite
                # parallelity is not enough

                if not is_opposite_normal_normal(a_normal, b_normal):
                    continue

                result = polygon_polygon_overlap(a_points, b_points, a_normal, tolerance, minimum_area)

                # this is not always an accurate representation of the interface
                # if the polygon has holes
                # the interface is incorrect

                if result:
                    points, frame, area, matrix_to_local, matrix_to_world = result

                    # if the result exists, but the faces have holes
                    # compute the holes in the intersection polygon

                    holes = brepface_brepface_overlap_holes(a_face, b_face, matrix_to_local, matrix_to_world, minimum_area)

                    contact = contacttype(points=points, frame=frame, size=area, holes=holes)
                    contacts.append(contact)

    return contacts


def polygon_polygon_overlap(
    a_points: list[Point] | list[list[float]],
    b_points: list[Point] | list[list[float]],
    normal: Vector,
    tolerance: float,
    minimum_area: float,
) -> Optional[tuple[list[Point], Frame, float, Transformation, Transformation]]:
    """Compute the overlap between two polygons defined by their corner points.

    Parameters
    ----------
    a_points
        The corner points of the first polygon.
    b_points
        The corner points of the second polygon.
    normal
        The normal vector defining the desired orientation of the local coordinate frame.
    tolerance
        Maximum deviation from the perfectly flat interface plane.
    minimum_area
        Minimum area of the overlap polygon.

    Returns
    -------
    tuple[list[Point], Frame, float, Transformation, Transformation] | None
        The corner points of the overlap polygon, the local coordinate frame, the area of the overlap polygon,
        the transformation to local coordinates, and the transformation to world coordinates.
        Returns None if there is no valid overlap.

    """
    # this ensures that a shared frame is used to do the interface calculations
    frame = Frame(*bestfit_frame_numpy(a_points + b_points))

    # the frame should be oriented along the normal of the "a" face
    # this will align the interface frame with the resulting interaction edge
    # which is important for calculations with solvers such as CRA
    if frame.zaxis.dot(normal) < 0:
        frame.invert()

    # compute the transformation to frame coordinates
    matrix_to_local = Transformation.from_change_of_basis(Frame.worldXY(), frame)
    matrix_to_world = matrix_to_local.inverted()

    a_projected = transform_points(a_points, matrix_to_local)
    b_projected = transform_points(b_points, matrix_to_local)

    p0 = ShapelyPolygon(a_projected)
    p1 = ShapelyPolygon(b_projected)

    if any(fabs(point[2]) > tolerance for point in a_projected + b_projected):
        return

    if p0.area < minimum_area or p1.area < minimum_area:
        # at least one of the face polygons is too small
        return

    if not p0.intersects(p1):
        # if the polygons don't intersect
        # there can't be an interface
        return

    intersection: ShapelyPolygon = p0.intersection(p1)  # type: ignore
    area = intersection.area

    if area < minimum_area:
        # the interface area is too small
        return

    coords = [[x, y, 0.0] for x, y, _ in intersection.exterior.coords]
    points = [Point(*xyz) for xyz in transform_points(coords, matrix_to_world)[:-1]]

    frame = Frame(centroid_polygon(points), frame.xaxis, frame.yaxis)

    return points, frame, area, matrix_to_local, matrix_to_world


def brepface_brepface_overlap_holes(
    a,
    b,
    matrix_to_local,
    matrix_to_world,
    minimum_area,
) -> Optional[list[Polygon]]:
    """Compute the holes in the overlap between two brep faces.

    Parameters
    ----------
    a : BrepFace
        The first brep face.
    b : BrepFace
        The second brep face.
    matrix_to_local : Transformation
        The transformation to local coordinates.
    matrix_to_world : Transformation
        The transformation to world coordinates.
    minimum_area : float
        Minimum area of a hole to be considered.

    Returns
    -------
    list[Polygon] | None
        The holes in the overlap polygon, or None if there are no holes.

    """
    a_polygons = a.to_polygons()
    a_boundary = transform_points(a_polygons[0].points, matrix_to_local)
    a_holes = [transform_points(polygon.points, matrix_to_local) for polygon in a_polygons[1:]]

    b_polygons = b.to_polygons()
    b_boundary = transform_points(b_polygons[0].points, matrix_to_local)
    b_holes = [transform_points(polygon.points, matrix_to_local) for polygon in b_polygons[1:]]

    a_shapely = ShapelyPolygon(a_boundary, holes=a_holes)
    b_shapely = ShapelyPolygon(b_boundary, holes=b_holes)

    intersection: ShapelyPolygon = a_shapely.intersection(b_shapely)  # type: ignore
    area = intersection.area

    if area < minimum_area:
        # the interface area is too small
        return

    holes = [[[x, y, 0.0] for x, y, _ in interior.coords] for interior in intersection.interiors]
    holes = [Polygon(transform_points(hole, matrix_to_world)[:-1]) for hole in holes]

    return holes
