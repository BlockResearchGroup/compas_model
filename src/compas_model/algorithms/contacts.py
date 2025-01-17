from math import fabs

from shapely.geometry import Polygon as ShapelyPolygon

from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Transformation
from compas.geometry import bestfit_frame_numpy
from compas.geometry import centroid_polygon
from compas.geometry import is_parallel_vector_vector
from compas.geometry import transform_points
from compas_model.interactions import Contact


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
    For equilibrium calculations with CRA, it is important that interface frames are aligned
    with the direction of the (interaction) edges on which they are stored.

    This means that if the bestfit frame does not align with the normal of the base source frame,
    it will be inverted, such that it corresponds to whatever edge is created from this source to a target.

    """
    world = Frame.worldXY()
    interfaces: list[Contact] = []

    for a_face in a.faces():
        a_points = a.face_coordinates(a_face)
        a_normal = a.face_normal(a_face)

        for b_face in b.faces():
            b_points = b.face_coordinates(b_face)
            b_normal = b.face_normal(b_face)

            # perhaps this should be an independent tolerance setting
            if not is_parallel_vector_vector(a_normal, b_normal, tol=tolerance):
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
            interface = Contact(points=points, frame=frame, size=area)
            interfaces.append(interface)

    return interfaces


# def identify_contact_interactions(model, tolerance=1, max_distance=1, min_area=0.1, interaction_type=None):
#     # type: (Model, float, float, float, Type[Interaction]) -> None
#     """Identify the contact interfaces between the elements of a model.

#     Parameters
#     ----------
#     model
#     deflection
#     tolerance
#     max_distance
#     interaction_type

#     Returns
#     -------
#     None

#     """
#     tol = Tolerance()

#     deflection = tol.lineardeflection
#     interaction_type = interaction_type or Contact

#     node_geometry = {}

#     for u in model.graph.nodes():
#         element_A: Element = model.graph.node_element(u)  # type: ignore

#         if u not in node_geometry:
#             if isinstance(element_A.geometry, Mesh):
#                 node_geometry[u] = Brep.from_mesh(element_A.geometry)
#             else:
#                 node_geometry[u] = element_A.geometry

#         A: Brep = node_geometry[u]

#         for v in model.graph.nodes():
#             if u == v:
#                 continue

#             if model.graph.has_edge((u, v), directed=False):
#                 continue

#             element_B: Element = model.graph.node_element(v)  # type: ignore

#             if v not in node_geometry:
#                 if isinstance(element_B.geometry, Mesh):
#                     node_geometry[v] = Brep.from_mesh(element_B.geometry)
#                 else:
#                     node_geometry[v] = element_B.geometry

#             B: Brep = node_geometry[v]

#             faces_A, faces_B = A.overlap(B, deflection=deflection, tolerance=tolerance)  # type: ignore
#             faces_A: list[BrepFace]
#             faces_B: list[BrepFace]

#             if faces_A and faces_B:

#                 for face_A in faces_A:
#                     poly_A = face_A.to_polygon()
#                     normal_A = poly_A.normal.unitized()
#                     xaxis = poly_A.points[1] - poly_A.points[0]
#                     frame_A = Frame(poly_A.centroid, xaxis, normal_A.cross(xaxis))

#                     matrix = Transformation.from_change_of_basis(world, frame_A)
#                     projected = transform_points(poly_A.points, matrix)
#                     projection_A = ShapelyPolygon(projected)

#                     for face_B in faces_B:
#                         poly_B = face_B.to_polygon()
#                         normal_B = poly_B.normal.unitized()

#                         if not tol.is_close(abs(normal_A.dot(normal_B)), 1.0):
#                             continue

#                         projected = transform_points(poly_B.points, matrix)
#                         projection_B = ShapelyPolygon(projected)

#                         if not all(abs(point[2]) < max_distance for point in projected):
#                             continue

#                         if projection_B.area < min_area:
#                             continue

#                         if not projection_A.intersects(projection_B):
#                             continue

#                         intersection = projection_A.intersection(projection_B)
#                         area = intersection.area

#                         if area < min_area:
#                             continue

#                         coords = [[x, y, 0.0] for x, y, _ in intersection.exterior.coords]
#                         coords = transform_points(coords, matrix.inverted())[:-1]

#                         poly = Polygon(coords)
#                         interaction = interaction_type(geometry=poly, frame=Frame(poly.centroid, frame_A.xaxis, frame_A.yaxis))

#                         # do something with the interactions
#                         model.add_interaction(element_A, element_B, interaction=interaction)
