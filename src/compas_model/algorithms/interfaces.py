from math import fabs

from shapely.geometry import Polygon as ShapelyPolygon

from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import bestfit_frame_numpy
from compas.geometry import centroid_polygon
from compas.geometry import is_colinear
from compas.geometry import is_coplanar
from compas.geometry import is_parallel_vector_vector
from compas.geometry import transform_points
from compas.itertools import window
from compas_model.elements import BlockGeometry
from compas_model.interactions import ContactInterface
from compas_model.models import Model

from .nnbrs import find_nearest_neighbours


def model_interfaces(
    model: Model,
    nmax: int = 10,
    tmax: float = 1e-6,
    amin: float = 1e-2,
    nnbrs_dims: int = 3,
) -> None:
    """Identify the interfaces between the blocks of an assembly.

    Parameters
    ----------
    model : :class:`Model`
        A model containing blocks with mesh geometry.
    nmax : int, optional
        Maximum number of neighbours per block.
    tmax : float, optional
        Maximum deviation from the perfectly flat interface plane.
    amin : float, optional
        Minimum area of a "face-face" interface.

    Returns
    -------
    None

    Notes
    -----
    Interface planes are computed from the bestfit frame of the combined points of two faces.

    """
    node_index = {node: index for index, node in enumerate(model.graph.nodes())}
    index_node = {index: node for index, node in enumerate(model.graph.nodes())}

    blocks: list[BlockGeometry] = [model.graph.node_element(node).modelgeometry for node in model.graph.nodes()]

    nmax = min(nmax, len(blocks))

    block_cloud = [block.centroid for block in blocks]
    block_nnbrs = find_nearest_neighbours(block_cloud, nmax, dims=nnbrs_dims)

    model.graph.edge = {node: {} for node in model.graph.nodes()}

    for node in model.graph.nodes():
        i = node_index[node]

        block = blocks[i]
        nbrs = block_nnbrs[i][1]

        for j in nbrs:
            n = index_node[j]

            if n == node:
                continue

            if model.graph.has_edge((n, node), directed=False):
                continue

            nbr = blocks[j]

            interfaces = mesh_mesh_interfaces(block, nbr, tmax, amin)

            if interfaces:
                # this can't be stored under interactions
                # it should be in an atteibute called "interfaces"
                # there can also be "collisions", "overlaps", "..."
                model.graph.add_edge(node, n, interactions=interfaces)


def mesh_mesh_interfaces(
    a: Mesh,
    b: Mesh,
    tmax: float = 1e-6,
    amin: float = 1e-1,
) -> list[ContactInterface]:
    """Compute all face-face contact interfaces between two meshes.

    Parameters
    ----------
    a : :class:`Mesh`
        The source mesh.
    b : :class:`Mesh`
        The target mesh.
    tmax : float, optional
        Maximum deviation from the perfectly flat interface plane.
    amin : float, optional
        Minimum area of a "face-face" interface.

    Returns
    -------
    list[:class:`ContactInterface`]

    Notes
    -----
    For equilibrium calculations with CRA, it is important that interface frames are aligned
    with the direction of the (interaction) edges on which they are stored.

    This means that if the bestfit frame does not align with the normal of the base source frame,
    it will be inverted, such that it corresponds to whatever edge is created from this source to a target.

    """
    world = Frame.worldXY()
    interfaces: list[ContactInterface] = []

    for face in a.faces():
        a_points = a.face_coordinates(face)
        a_normal = a.face_normal(face)

        for test in b.faces():
            b_points = b.face_coordinates(test)
            b_normal = b.face_normal(test)

            if not is_parallel_vector_vector(a_normal, b_normal):
                continue

            # this ensures that a shared frame is used to do the interface calculations
            # the frame should be oriented along the normal of the "a" face
            # this will align the interface frame with the resulting interaction edge
            # whgich is important for calculations with solvers such as CRA
            frame = Frame(*bestfit_frame_numpy(a_points + b_points))
            if frame.zaxis.dot(a_normal) < 0:
                frame.invert()

            matrix = Transformation.from_change_of_basis(world, frame)

            a_projected = transform_points(a_points, matrix)
            p0 = ShapelyPolygon(a_projected)

            b_projected = transform_points(b_points, matrix)
            p1 = ShapelyPolygon(b_projected)

            projected = a_projected + b_projected

            if not all(fabs(point[2]) < tmax for point in projected):
                continue

            if p0.area < amin or p1.area < amin:
                continue

            if not p0.intersects(p1):
                continue

            intersection: ShapelyPolygon = p0.intersection(p1)
            area = intersection.area

            if area < amin:
                continue

            coords = [[x, y, 0.0] for x, y, _ in intersection.exterior.coords]
            coords = transform_points(coords, matrix.inverted())[:-1]

            # this is not always an accurate representation of the interface
            # if the polygon has holes
            # the interface is incorrect

            interface = ContactInterface(
                size=area,
                points=coords,
                frame=Frame(
                    centroid_polygon(coords),
                    frame.xaxis,
                    frame.yaxis,
                ),
            )

            interfaces.append(interface)

    return interfaces


def merge_coplanar_interfaces(model: Model, tol: float = 1e-6) -> None:
    """Merge connected coplanar interfaces between pairs of blocks.

    Parameters
    ----------
    model : :class:`compas_model.model.Model`
        A block model with identified interfaces.
    tol : float, optional
        The tolerance for coplanarity.

    Returns
    -------
    None

    """
    for edge in model.graph.edges():
        interfaces: list[ContactInterface] = model.graph.edge_attribute(edge, "interfaces")

        if interfaces:
            polygons = []
            for interface in interfaces:
                points = []
                for a, b, c in window(interface.points + interface.points[:2], 3):
                    if not is_colinear(a, b, c):
                        points.append(b)

                polygons.append(Polygon(points))

            temp = Mesh.from_polygons(polygons)
            try:
                temp.unify_cycles()
            except Exception:
                continue

            reconstruct = False

            while True:
                if temp.number_of_faces() < 2:
                    break

                has_merged = False

                for face in temp.faces():
                    nbrs = temp.face_neighbors(face)
                    points = temp.face_coordinates(face)
                    vertices = temp.face_vertices(face)

                    for nbr in nbrs:
                        for vertex in temp.face_vertices(nbr):
                            if vertex not in vertices:
                                points.append(temp.vertex_coordinates(vertex))

                        if is_coplanar(points, tol=tol):
                            temp.merge_faces([face, nbr])
                            has_merged = True
                            reconstruct = True
                            break

                    if has_merged:
                        break

                if not has_merged:
                    break

            if reconstruct:
                interfaces = []
                for face in temp.faces():
                    points = temp.face_coordinates(face)
                    area = temp.face_area(face)
                    frame = Frame.from_plane(Plane(temp.face_centroid(face), temp.face_normal(face)))
                    interface = ContactInterface(
                        points=points,
                        frame=frame,
                        size=area,
                        mesh=Mesh.from_polygons([points]),
                    )
                    interfaces.append(interface)

                model.graph.edge_attribute(edge, "interfaces", interfaces)
