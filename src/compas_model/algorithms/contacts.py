from math import fabs
from typing import Optional

from shapely.geometry import Polygon as ShapelyPolygon

from compas.datastructures import Mesh

# from compas.geometry import Frame
# from compas.geometry import bestfit_frame_numpy
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import bestfit_frame_numpy
from compas.geometry import centroid_polygon
from compas.geometry import cross_vectors
from compas.geometry import dot_vectors
from compas.geometry import length_vector
from compas.geometry import transform_points
from compas.tolerance import TOL
from compas.tolerance import Tolerance
from compas_model.interactions import Contact


def is_opposite_vector_vector(u, v, tol=None):
    return TOL.is_zero(length_vector(cross_vectors(u, v)), tol) and TOL.is_close(dot_vectors(u, v), -1)


def mesh_mesh_contacts(
    a: Mesh,
    b: Mesh,
    tolerance: float = 1e-6,
    minimum_area: float = 1e-1,
) -> list[Contact]:
    """Compute all face-face contact interfaces between two meshes.

    Parameters
    ----------
    a : :class:`Mesh`
        The source mesh.
    b : :class:`Mesh`
        The target mesh.
    tolerance : float, optional
        Maximum deviation from the perfectly flat interface plane.
    minimum_area : float, optional
        Minimum area of a "face-face" interface.

    Returns
    -------
    list[:class:`Contact`]

    Notes
    -----
    For equilibrium calculations (e.g. with CRA), it is important that interface frames are aligned
    with the direction of the (interaction) edges on which they are stored.

    This means that if the bestfit frame does not align with the normal of the base source frame,
    it will be inverted, such that it corresponds to whatever edge is created from this source to a target.

    """
    # tolerance is used both for parallelity and for copenetration
    # perhaps two different thresholds should be used

    world = Frame.worldXY()
    contacts: list[Contact] = []

    for a_face in a.faces():
        a_points = a.face_coordinates(a_face)
        a_normal = a.face_normal(a_face)

        for b_face in b.faces():
            b_points = b.face_coordinates(b_face)
            b_normal = b.face_normal(b_face)

            # normals shoul actually be exactly opposite
            # parallelity is not enough
            if not is_opposite_vector_vector(a_normal, b_normal, tol=tolerance):
                continue

            # this ensures that a shared frame is used to do the interface calculations
            frame = Frame(*bestfit_frame_numpy(a_points + b_points))

            # the frame should be oriented along the normal of the "a" face
            # this will align the interface frame with the resulting interaction edge
            # which is important for calculations with solvers such as CRA
            if frame.zaxis.dot(a_normal) < 0:
                frame.invert()

            # compute the transformation to frame coordinates
            matrix = Transformation.from_change_of_basis(world, frame)

            a_projected = transform_points(a_points, matrix)
            b_projected = transform_points(b_points, matrix)

            p0 = ShapelyPolygon(a_projected)
            p1 = ShapelyPolygon(b_projected)

            if any(fabs(point[2]) > tolerance for point in a_projected + b_projected):
                continue

            if p0.area < minimum_area or p1.area < minimum_area:
                # at least one of the face polygons is too small
                continue

            if not p0.intersects(p1):
                # if the polygons don't intersect
                # there can't be an interface
                continue

            intersection: ShapelyPolygon = p0.intersection(p1)
            area = intersection.area

            if area < minimum_area:
                # the interface area is too small
                continue

            coords = [[x, y, 0.0] for x, y, _ in intersection.exterior.coords]
            points = transform_points(coords, matrix.inverted())[:-1]
            frame = Frame(centroid_polygon(points), frame.xaxis, frame.yaxis)

            # this is not always an accurate representation of the interface
            # if the polygon has holes
            # the interface is incorrect
            contact = Contact(points=points, frame=frame, size=area)
            contacts.append(contact)

    return contacts


def brep_brep_contacts(
    a: Brep,
    b: Brep,
    tolerance: float = 1e-6,
    minimum_area: float = 1e-1,
    deflection: Optional[float] = None,
) -> list[Contact]:
    """Compute all face-face contact interfaces between two meshes.

    Parameters
    ----------
    a : :class:`Brep`
        The source brep.
    b : :class:`Brep`
        The target brep.
    tolerance : float, optional
        Maximum deviation from the perfectly flat interface plane.
    minimum_area : float, optional
        Minimum area of a "face-face" interface.

    Returns
    -------
    list[:class:`Contact`]

    Notes
    -----
    For equilibrium calculations (e.g. with CRA), it is important that interface frames are aligned
    with the direction of the (interaction) edges on which they are stored.

    This means that if the bestfit frame does not align with the normal of the base source frame,
    it will be inverted, such that it corresponds to whatever edge is created from this source to a target.

    """
    contacts: list[Contact] = []

    deflection = deflection or Tolerance().lineardeflection

    a_faces, b_faces = a.overlap(b, linear_deflection=deflection, tolerance=tolerance)

    if a_faces and b_faces:
        for a_face in a_faces:
            a_poly: Polygon = a_face.to_polygon()

            if a_face.area < minimum_area:
                continue

            a_points = a_poly.points
            a_normal = a_poly.normal.unitized()

            for b_face in b_faces:
                b_poly: Polygon = b_face.to_polygon()

                if b_face.area < minimum_area:
                    continue

                b_points = b_poly.points
                b_normal = b_poly.normal.unitized()

                # if not Tolerance().is_close(abs(a_poly.normal.unitized().dot(b_poly.normal.unitized())), 1):
                #     continue

                # brep_c: Brep = Brep.from_boolean_intersection(brep_a, brep_b)

                # if brep_c.area < minimum_area:
                #     continue

                # poly_c = brep_c.to_polygons()[0]
                # mesh_c = brep_c.to_tesselation()[0]

                result = polygon_polygon_overlap(a_points, a_normal, b_points, b_normal, tolerance, minimum_area)

                if result:
                    points, frame, area = result
                    contact = Contact(points=points, frame=frame, size=area)
                    contacts.append(contact)

    return contacts


def polygon_polygon_overlap(a_points, a_normal, b_points, b_normal, tolerance, minimum_area):
    if not is_opposite_vector_vector(a_normal, b_normal, tol=tolerance):
        return

    frame = Frame(*bestfit_frame_numpy(a_points + b_points))

    if frame.zaxis.dot(a_normal) < 0:
        frame.invert()

    matrix = Transformation.from_change_of_basis(Frame.worldXY(), frame)

    a_projected = transform_points(a_points, matrix)
    b_projected = transform_points(b_points, matrix)

    p0 = ShapelyPolygon(a_projected)
    p1 = ShapelyPolygon(b_projected)

    if any(fabs(point[2]) > tolerance for point in a_projected + b_projected):
        return

    if p0.area < minimum_area or p1.area < minimum_area:
        return

    if not p0.intersects(p1):
        return

    intersection: ShapelyPolygon = p0.intersection(p1)
    area = intersection.area

    if area < minimum_area:
        return

    coords = [[x, y, 0.0] for x, y, _ in intersection.exterior.coords]
    points = transform_points(coords, matrix.inverted())[:-1]
    frame = Frame(centroid_polygon(points), frame.xaxis, frame.yaxis)

    return points, frame, area
