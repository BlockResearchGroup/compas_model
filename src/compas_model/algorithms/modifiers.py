from typing import Optional

from compas.datastructures import Mesh


def slice(geometry, slice_plane):
    """Slice the target geometry by the slice plane.

    Parameters
    ----------
    geometry : Brep or Mesh
        The geometry to be affected. The same geometry can be modified multiple times.

    slice_plane : Plane
        The plane to slice the geometry.

    Returns
    -------
    Brep or Mesh
        The sliced geometry.
    """
    try:
        split_meshes: Optional[list] = geometry.slice(slice_plane)
        return split_meshes[0] if split_meshes else geometry
    except Exception:
        print("SlicerModifier is not successful.")
        return geometry


def boolean_difference(target_geometry, source_geometry):
    """Perform boolean difference on the target geometry.

    Parameters
    ----------
    target_geometry : Brep or Mesh
        The geometry to be affected.
    source_geometry : Brep or Mesh
        The geometry to subtract.

    Returns
    -------
    Brep or Mesh
        The geometry after boolean difference.
    """
    from compas_cgal.booleans import boolean_difference_mesh_mesh

    target_geometry_copy = target_geometry.copy()
    source_geometry_copy = source_geometry.copy()
    target_geometry_copy.unify_cycles()
    source_geometry_copy.unify_cycles()

    A = target_geometry_copy.to_vertices_and_faces(triangulated=True)
    B = source_geometry_copy.to_vertices_and_faces(triangulated=True)
    V, F = boolean_difference_mesh_mesh(A, B)
    return Mesh.from_vertices_and_faces(V, F) if len(V) > 0 and len(F) > 0 else target_geometry_copy
