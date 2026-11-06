import numpy as np

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Polygon
from compas.geometry import bestfit_frame
from compas.linalg import cross_vectors
from compas.linalg import dot_vectors
from compas.linalg import length_vector
from compas.tolerance import TOL
from compas.typing import PointsLike
from compas.typing import VectorLike
from compas_model.geometry import NonCoplanarRegionsError
from compas_model.geometry import PlanarRegion
from compas_model.geometry import intersection_planar_region_planar_region
from compas_model.interactions import Contact


def is_opposite_vector_vector(u: VectorLike, v: VectorLike, tol: float | None = None) -> bool | np.bool_:
    """Check if two vectors are opposite.

    Parameters
    ----------
    u
        The first vector.
    v
        The second vector.
    tol
        Tolerance for the check.

    Returns
    -------
    bool | numpy.bool_
        True if the vectors are opposite.

    Notes
    -----
    Two vectors are considered parallel if their cross product is zero.
    They are considered opposite if they are parallel and their dot product is -1.

    """
    return TOL.is_zero(length_vector(cross_vectors(u, v)), tol) and TOL.is_close(dot_vectors(u, v), -1, rtol=1e-3)


def is_opposite_normal_normal(u: VectorLike, v: VectorLike) -> bool | np.bool_:
    """Check if two normals are opposite.

    Parameters
    ----------
    u
        The first normal.
    v
        The second normal.

    Returns
    -------
    bool | numpy.bool_
        True if the normals are opposite.

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
    contacttype: type[Contact] = Contact,
) -> list[Contact]:
    """Compute all face-face contact interfaces between two meshes.

    Parameters
    ----------
    a
        The source mesh.
    b
        The target mesh.
    tolerance
        Maximum deviation from the perfectly flat interface plane.
    minimum_area
        Minimum area of a "face-face" interface.
    contacttype
        The contact class to use for the generated interfaces. Its constructor
        should accept one `PlanarRegion` positional argument.

    Returns
    -------
    list[Contact]
        The detected contact interfaces.

    Raises
    ------
    ValueError
        If `tolerance` or `minimum_area` is negative.

    Notes
    -----
    For equilibrium calculations (e.g. with CRA), it is important that interface frames are aligned
    with the direction of the (interaction) edges on which they are stored.

    This means that if the bestfit frame does not align with the normal of the base source frame,
    it will be inverted, such that it corresponds to whatever edge is created from this source to a target.

    """
    _validate_contact_options(tolerance, minimum_area)

    contacts: list[Contact] = []

    for a_face in a.faces():
        a_points = a.face_coordinates(a_face)
        a_normal = a.face_normal(a_face)

        for b_face in b.faces():
            b_points = b.face_coordinates(b_face)
            b_normal = b.face_normal(b_face)

            if not is_opposite_normal_normal(a_normal, b_normal):
                continue

            regions = polygon_polygon_overlap(a_points, b_points, a_normal, tolerance, minimum_area)  # type: ignore
            contacts.extend(_contacts_from_regions(regions, contacttype))

    return contacts


def brep_brep_contacts(
    a: Brep,
    b: Brep,
    tolerance: float = 1e-6,
    minimum_area: float = 1e-1,
    deflection: float | None = None,
    contacttype: type[Contact] = Contact,
) -> list[Contact]:
    """Compute all face-face contact interfaces between two breps.

    Parameters
    ----------
    a
        The source brep.
    b
        The target brep.
    tolerance
        Maximum deviation from the perfectly flat interface plane.
    minimum_area
        Minimum area of a "face-face" interface.
    deflection
        Linear deflection used to compute face overlaps.
    contacttype
        The contact class to use for the generated interfaces. Its constructor
        should accept one `PlanarRegion` positional argument.

    Returns
    -------
    list[Contact]
        The detected contact interfaces.

    Raises
    ------
    ValueError
        If `tolerance` or `minimum_area` is negative, or `deflection` is not
        positive.

    Notes
    -----
    For equilibrium calculations (e.g. with CRA), it is important that interface frames are aligned
    with the direction of the (interaction) edges on which they are stored.

    This means that if the bestfit frame does not align with the normal of the base source frame,
    it will be inverted, such that it corresponds to whatever edge is created from this source to a target.

    """
    _validate_contact_options(tolerance, minimum_area)
    if deflection is not None and deflection <= 0:
        raise ValueError("The deflection should be greater than zero.")

    contacts: list[Contact] = []

    deflection = deflection or TOL.lineardeflection

    # the parameter name linear_deflection is specific to OCC
    a_faces, b_faces = a.overlap(b, linear_deflection=deflection, tolerance=tolerance)  # type: ignore

    if a_faces and b_faces:
        for a_face in a_faces:
            if a_face.area < minimum_area:
                continue

            a_polygons: list[Polygon] = a_face.to_polygons()  # type: ignore[reportAttributeAccessIssue]
            a_normal = a_polygons[0].normal().unitized()

            for b_face in b_faces:
                if b_face.area < minimum_area:
                    continue

                b_polygons: list[Polygon] = b_face.to_polygons()  # type: ignore[reportAttributeAccessIssue]
                b_normal = b_polygons[0].normal().unitized()

                if not is_opposite_normal_normal(a_normal, b_normal):
                    continue

                regions = _polygon_polygon_overlap(
                    a_polygons[0],
                    b_polygons[0],
                    a_normal,
                    tolerance,
                    minimum_area,
                    a_holes=a_polygons[1:],
                    b_holes=b_polygons[1:],
                )
                contacts.extend(_contacts_from_regions(regions, contacttype))

    return contacts


def polygon_polygon_overlap(
    a_points: PointsLike,
    b_points: PointsLike,
    normal: VectorLike,
    tolerance: float,
    minimum_area: float,
) -> list[PlanarRegion]:
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
    list[PlanarRegion]
        The connected positive-area overlap regions. Boundary-only contact
        returns an empty list.

    Raises
    ------
    ValueError
        If `tolerance` or `minimum_area` is negative, or an input boundary
        cannot form a valid planar region.

    """
    _validate_contact_options(tolerance, minimum_area)
    polygon_a = Polygon(a_points)
    polygon_b = Polygon(b_points)
    return _polygon_polygon_overlap(polygon_a, polygon_b, normal, tolerance, minimum_area)


def _polygon_polygon_overlap(
    polygon_a: Polygon,
    polygon_b: Polygon,
    normal: VectorLike,
    tolerance: float,
    minimum_area: float,
    a_holes: list[Polygon] | None = None,
    b_holes: list[Polygon] | None = None,
) -> list[PlanarRegion]:
    point, xaxis, yaxis = bestfit_frame(polygon_a.points)
    frame = Frame(point, xaxis, yaxis)
    if frame.zaxis.dot(normal) < 0:
        frame.invert()

    try:
        region_a = PlanarRegion(polygon_a, holes=a_holes, frame=frame)
        region_b = PlanarRegion(polygon_b, holes=b_holes)
        return intersection_planar_region_planar_region(
            region_a,
            region_b,
            tolerance=tolerance,
            minimum_area=minimum_area,
        )
    except NonCoplanarRegionsError:
        return []


def _contacts_from_regions(regions: list[PlanarRegion], contacttype: type[Contact]) -> list[Contact]:
    return [contacttype(region) for region in regions]


def _validate_contact_options(tolerance: float, minimum_area: float) -> None:
    if tolerance < 0:
        raise ValueError("The tolerance should be greater than or equal to zero.")
    if minimum_area < 0:
        raise ValueError("The minimum area should be greater than or equal to zero.")
