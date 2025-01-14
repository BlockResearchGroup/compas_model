from typing import Optional
from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Plane


def slice(geometry: Union[Brep, Mesh], slice_plane: Plane) -> Union[Brep, Mesh]:
    """Slice the target geometry by the slice plane.
    NOTE: Original geometry is returned if slicing is not successful.

    Parameters
    ----------
    geometry : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
        The geometry to be affected. The same geometry can be modified multiple times.
    slice_plane : :class:`compas.geometry.Plane`
        The plane to slice the geometry.

    Returns
    -------
    :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
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
    NOTE: Original geometry is returned if boolean difference is not successful.

    Parameters
    ----------
    target_geometry : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
        The geometry to be affected.
    source_geometry : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
        The geometry to subtract.

    Returns
    -------
    :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
        The geometry after boolean difference.
    """

    target_geometry.boolean_difference(source_geometry)

    from compas_cgal.booleans import boolean_difference_mesh_mesh

    target_geometry_copy = target_geometry.copy()
    source_geometry_copy = source_geometry.copy()

    # unify_cycles method cycles often fail when they are cut several times.
    # target_geometry_copy.unify_cycles()
    # source_geometry_copy.unify_cycles()

    A = target_geometry_copy.to_vertices_and_faces(triangulated=True)
    B = source_geometry_copy.to_vertices_and_faces(triangulated=True)
    V, F = boolean_difference_mesh_mesh(A, B)
    mesh: Mesh = Mesh.from_vertices_and_faces(V, F) if len(V) > 0 and len(F) > 0 else target_geometry_copy
    return mesh
