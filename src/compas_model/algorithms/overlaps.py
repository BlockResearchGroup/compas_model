from compas.geometry import Brep
from compas.tolerance import TOL
from compas_model.interactions import ContactInterface
from compas_model.models import Model

from .nnbrs import find_nearest_neighbours


def model_overlaps(
    model: Model,
    deflection=None,
    tolerance=1,
    nmax: int = 10,
    tmax: float = 1e-6,
    amin: float = 1e-2,
    nnbrs_dims: int = 3,
):
    """Identify the interfaces between the blocks of an assembly.

    Parameters
    ----------
    assembly : compas_assembly.datastructures.Assembly
        An assembly of discrete blocks.
    nmax : int, optional
        Maximum number of neighbours per block.
    tmax : float, optional
        Maximum deviation from the perfectly flat interface plane.
    amin : float, optional
        Minimum area of a "face-face" interface.

    Returns
    -------
    :class:`Assembly`

    """
    deflection = deflection or TOL.lineardeflection

    node_index = {node: index for index, node in enumerate(model.graph.nodes())}
    index_node = {index: node for index, node in enumerate(model.graph.nodes())}

    geometries: list[Brep] = [model.graph.node_element(node).modelgeometry for node in model.graph.nodes()]

    nmax = min(nmax, len(geometries))
    cloud = [geometry.centroid for geometry in geometries]
    nnbrs = find_nearest_neighbours(cloud, nmax, dims=nnbrs_dims)

    model.graph.edge = {node: {} for node in model.graph.nodes()}

    for u in model.graph.nodes():
        i = node_index[u]
        A = geometries[i]

        nbrs = nnbrs[i][1]

        for j in nbrs:
            v = index_node[j]

            if u == v:
                continue

            if model.graph.has_edge((u, v), directed=False):
                continue

            B = geometries[j]

            overlaps = brep_brep_overlaps(A, B, deflection=deflection, tolerance=tolerance, tmax=tmax, amin=amin)

            if overlaps:
                model.graph.add_edge(u, v, interactions=overlaps)

    return model


def brep_brep_overlaps(
    A: Brep,
    B: Brep,
    deflection=None,
    tolerance=1,
    tmax: float = 1e-6,
    amin: float = 1e-2,
) -> list[ContactInterface]:
    """Compute all face-face contact interfaces between two meshes.

    Parameters
    ----------
    a : :class:`Block`
    b : :class:`Block`
    tmax : float, optional
        Maximum deviation from the perfectly flat interface plane.
    amin : float, optional
        Minimum area of a "face-face" interface.

    Returns
    -------
    List[:class:`ContactInterface`]

    Notes
    -----
    For equilibrium calculations with CRA, it is important that interface frames are aligned
    with the direction of the (interaction) edges on which they are stored.

    This means that if the

    """

    try:
        from compas_occ.brep import OCCBrepFace as BrepFace
    except ImportError:
        raise ImportError("compas_occ is required for this functionality. Please install it via conda.")

    faces_A, faces_B = A.overlap(B, deflection=deflection, tolerance=tolerance)
    faces_A: list[BrepFace]
    faces_B: list[BrepFace]

    overlaps: list[ContactInterface] = []

    if faces_A and faces_B:
        for face_A in faces_A:
            brep_A = Brep.from_brepfaces([face_A])

            if brep_A.area < amin:
                continue

            for face_B in faces_B:
                brep_B = Brep.from_brepfaces([face_B])

                if brep_B.area < amin:
                    continue

                brep_C: Brep = Brep.from_boolean_intersection(brep_A, brep_B)

                if brep_C.area < amin:
                    continue

                poly_C = brep_C.to_polygons()[0]
                mesh_C = brep_C.to_tesselation()[0]

                overlap = ContactInterface(points=poly_C.points, mesh=mesh_C)
                overlaps.append(overlap)

    return overlaps
