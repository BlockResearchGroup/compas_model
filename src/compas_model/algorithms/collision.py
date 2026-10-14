from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Point
from compas.geometry import Polyhedron
from compas_model.geometry import aabb_from_points
from compas_model.geometry import is_intersection_aabb_aabb
from compas_model.geometry import is_intersection_box_box

from ._coal import is_mesh_mesh_collision_coal
from ._occ import is_brep_brep_collision_occ


def is_box_box_collision(A: Box, B: Box) -> bool:
    """Determine whether two oriented boxes collide using separating axes."""
    return is_intersection_box_box(A, B)


def is_polyhedron_polyhedron_collision(A: Polyhedron, B: Polyhedron) -> bool:
    raise NotImplementedError


def is_mesh_mesh_collision(
    A: Mesh,
    B: Mesh,
    tolerance: float = 0.0,
    include_touching: bool = True,
) -> bool:
    """Determine whether two mesh surfaces collide using Coal.

    Parameters
    ----------
    A
        The first mesh.
    B
        The second mesh.
    tolerance
        The maximum surface separation considered a collision.
    include_touching
        If ``True``, touching mesh surfaces are considered colliding.

    Returns
    -------
    bool
        ``True`` if the triangulated mesh surfaces intersect or are separated
        by no more than ``tolerance``.

    Raises
    ------
    ImportError
        If the optional Coal backend is unavailable.
    NotImplementedError
        If ``include_touching`` is ``False``.
    ValueError
        If ``tolerance`` is negative or a mesh cannot form a valid triangle
        collision model.

    Notes
    -----
    Mesh faces are triangulated without modifying the input meshes. Meshes are
    treated as surfaces, not implicitly as solids: one closed mesh entirely
    inside another does not collide unless their surfaces intersect.

    Coal reports triangle contact but does not robustly distinguish all
    boundary-only contact from surface penetration. Excluding touching is
    therefore rejected instead of returning an ambiguous result.

    """
    if tolerance < 0:
        raise ValueError("The tolerance should be greater than or equal to zero.")
    if not include_touching:
        raise NotImplementedError("Precise mesh collision cannot currently exclude boundary-only contact.")
    return is_mesh_mesh_collision_coal(A, B, tolerance=tolerance)


def is_brep_brep_collision(
    A: Brep,
    B: Brep,
    tolerance: float = 0.0,
    include_touching: bool = True,
) -> bool:
    """Determine whether two COMPAS OCC BReps collide.

    Parameters
    ----------
    A
        The first BRep.
    B
        The second BRep.
    tolerance
        The maximum boundary separation considered a collision.
    include_touching
        If ``True``, boundary contact and solid containment are considered
        collisions. If ``False``, both BReps must be solids with positive
        common volume.

    Returns
    -------
    bool
        ``True`` if the BReps collide according to the selected semantics.

    Raises
    ------
    ImportError
        If the optional COMPAS OCC backend is unavailable.
    TypeError
        If either BRep does not use the COMPAS OCC backend.
    ValueError
        If ``tolerance`` is negative or either BRep has an empty or invalid
        native shape.
    NotImplementedError
        If touching is excluded for non-solids or with a positive tolerance.
    RuntimeError
        If Open CASCADE fails to complete the required query.

    Notes
    -----
    Default collision uses Open CASCADE's native shape-distance query. It
    reports zero distance for boundary intersection and for one solid contained
    in another. The comparison never uses less than Open CASCADE's own
    ``Precision::Confusion()`` resolution. Excluding touching uses the volume
    of the boolean intersection.

    """
    if tolerance < 0:
        raise ValueError("The tolerance should be greater than or equal to zero.")
    return is_brep_brep_collision_occ(A, B, tolerance=tolerance, include_touching=include_touching)


def is_mesh_mesh_collision_fast(
    A: Mesh,
    B: Mesh,
    tolerance: float = 0.0,
    include_touching: bool = True,
) -> bool:
    """Conservatively test two meshes for collision using their AABBs.

    Parameters
    ----------
    A
        The first mesh.
    B
        The second mesh.
    tolerance
        The maximum AABB separation considered a collision.
    include_touching
        If ``True``, AABBs that only touch are considered colliding.

    Returns
    -------
    bool
        ``False`` guarantees that the meshes do not intersect. ``True`` means
        that a more precise check may be required.

    Raises
    ------
    ValueError
        If either mesh has no vertices or ``tolerance`` is negative.

    Notes
    -----
    Mesh faces and topology are deliberately ignored. Therefore, overlapping
    AABBs can produce false positives but not false negatives, provided all
    mesh vertices bound the represented geometry.

    """
    vertices_a = A.vertices_attributes("xyz") or []
    vertices_b = B.vertices_attributes("xyz") or []
    box_a = aabb_from_points(Point(*xyz) for xyz in vertices_a if xyz is not None)
    box_b = aabb_from_points(Point(*xyz) for xyz in vertices_b if xyz is not None)
    return is_intersection_aabb_aabb(box_a, box_b, tolerance=tolerance, include_touching=include_touching)


def is_brep_brep_collision_fast(
    A: Brep,
    B: Brep,
    tolerance: float = 0.0,
    include_touching: bool = True,
) -> bool:
    """Conservatively test two BReps for collision using their AABBs.

    Parameters
    ----------
    A
        The first BRep.
    B
        The second BRep.
    tolerance
        The maximum AABB separation considered a collision.
    include_touching
        If ``True``, AABBs that only touch are considered colliding.

    Returns
    -------
    bool
        ``False`` guarantees that the BReps do not intersect. ``True`` means
        that a more precise check may be required.

    Raises
    ------
    ValueError
        If either BRep exposes no points or ``tolerance`` is negative.

    Notes
    -----
    Faces, edges, and analytic surfaces are not compared directly. Their
    extents are represented by the AABBs computed by the active COMPAS BRep
    backend, including extrema of curved geometry when supported by that
    backend.

    """
    return is_intersection_aabb_aabb(A.aabb, B.aabb, tolerance=tolerance, include_touching=include_touching)
