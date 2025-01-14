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

    is_brep0: bool = isinstance(target_geometry, Brep)
    is_brep1: bool = isinstance(source_geometry, Brep)

    if is_brep0 and is_brep1:
        try:
            return Brep.from_boolean_difference(target_geometry, source_geometry)
        except Exception:
            print("Boolean difference is not successful.")
            return target_geometry

    else:
        from compas_cgal.booleans import boolean_difference_mesh_mesh

        mesh0: Mesh = target_geometry.copy() if not is_brep0 else target_geometry.to_meshes()[0]
        mesh1: Mesh = source_geometry.copy() if not is_brep1 else source_geometry.to_meshes()[0]

        A = mesh0.to_vertices_and_faces(triangulated=True)
        B = mesh1.to_vertices_and_faces(triangulated=True)
        V, F = boolean_difference_mesh_mesh(A, B)
        mesh: Mesh = Mesh.from_vertices_and_faces(V, F) if len(V) > 0 and len(F) > 0 else mesh0
        return mesh
