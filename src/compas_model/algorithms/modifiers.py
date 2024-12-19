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
        if len(split_meshes) == 0:
            print("SlicerModifier is not successful, 0 meshes create, original mesh is returned.")
            return geometry
        return split_meshes[0]
    except Exception:
        print("SlicerModifier is not successful, I don't know why. Probably plane is coincident with the geometry or not intersecting.")
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
    Brep or Meshd_
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

    if V.size > 0 and F.size > 0:
        return Mesh.from_vertices_and_faces(V, F)
    else:
        print("Boolean difference is not successful, original mesh is returned.")
        return target_geometry
