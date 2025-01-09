from typing import Optional

from compas_occ.brep import OCCBrepFace as BrepFace

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Polygon
from compas.tolerance import TOL
from compas_model.algorithms.nnbrs import find_nearest_neighbours
from compas_model.interactions import ContactInterface
from compas_model.models import Model


def model_overlaps(
    model: Model,
    nmax: int = 10,
    amin: float = 1e-2,
    nnbrs_dims: int = 3,
    deflection: Optional[float] = None,
    tolerance: float = 1,
) -> None:
    """Identify the interfaces between the blocks of an assembly.

    Parameters
    ----------
    model : :class:`Model`
        A model of blocks represented by Breps.
    nmax : int, optional
        Maximum number of neighbours per block.
    amin : float, optional
        Minimum area of a "face-face" interface.
    nnbrs_dims : int, optional
        The number of dimensions for the nearest neighbours search.
    deflection : float, optional
        The allowable linear deflection for approximating a curved surface using a triangle mesh.
        Default is to use `compas.tolerance.TOL.lineardeflection`.
    tolerance : float, optional
        The tolerance for considering two surfaces overlapping.
        Default is to use `compas.tolerance.TOL.???`.

    Returns
    -------
    None

    """
    deflection = deflection or TOL.lineardeflection

    node_index = {node: index for index, node in enumerate(model.graph.nodes())}
    index_node = {index: node for index, node in enumerate(model.graph.nodes())}

    geometries: list[Brep] = [model.graph.node_element(node).modelgeometry for node in model.graph.nodes()]

    nmax = min(nmax, len(geometries))
    cloud = [geometry.centroid for geometry in geometries]
    nnbrs = find_nearest_neighbours(cloud, nmax, dims=nnbrs_dims)

    # reset edges
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

            overlaps = brep_brep_overlaps(A, B, deflection=deflection, tolerance=tolerance, amin=amin)

            if overlaps:
                model.graph.add_edge(u, v, interactions=overlaps)


def brep_brep_overlaps(
    A: Brep,
    B: Brep,
    deflection: Optional[float] = None,
    tolerance: float = 1,
    amin: float = 1e-2,
) -> list[ContactInterface]:
    """Compute all face-face contact interfaces between two meshes.

    Parameters
    ----------
    A : :class:`Brep`
        The source block.
    B : :class:`Brep`
        The target block.
    deflection : float, optional
        The allowable linear deflection for approximating a curved surface using a triangle mesh.
        Default is to use `compas.tolerance.TOL.lineardeflection`.
    tolerance : float, optional
        The tolerance for considering two surfaces overlapping.
        Default is to use `compas.tolerance.TOL.???`.
    amin : float, optional
        Minimum area of a "face-face" interface.

    Returns
    -------
    list[:class:`ContactInterface`]

    """
    faces_A: list[BrepFace]
    faces_B: list[BrepFace]

    overlaps: list[ContactInterface] = []

    faces_A, faces_B = A.overlap(B, deflection=deflection, tolerance=tolerance)

    brep_A: Brep
    brep_B: Brep
    brep_C: Brep
    poly_C: Polygon
    mesh_C: Mesh

    if faces_A and faces_B:
        for face_A in faces_A:
            brep_A = Brep.from_brepfaces([face_A])

            if brep_A.area < amin:  # is this only defined for OCC?
                continue

            for face_B in faces_B:
                brep_B = Brep.from_brepfaces([face_B])

                if brep_B.area < amin:  # is this only defined for OCC?
                    continue

                brep_C = Brep.from_boolean_intersection(brep_A, brep_B)

                if brep_C.area < amin:  # is this only defined for OCC?
                    continue

                poly_C = brep_C.to_polygons()[0]  # is this only defined for OCC?
                mesh_C = brep_C.to_tesselation()[0]  # is this only defined for OCC?

                overlap = ContactInterface(points=poly_C.points, mesh=mesh_C)
                overlaps.append(overlap)

    return overlaps


def merge_coplanar_overlaps():
    pass
