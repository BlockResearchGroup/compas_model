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
        if isinstance(geometry, Brep):
            geometry.make_solid()
            slice_plane_flipped = Plane(slice_plane.point, -slice_plane.normal)
            geometry.trim(slice_plane_flipped)
            return geometry
        else:
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

    if isinstance(target_geometry, Brep) and isinstance(source_geometry, Brep):
        try:
            return Brep.from_boolean_difference(target_geometry, source_geometry)
        except Exception:
            print("Boolean difference is not successful.")
            return target_geometry
    else:
        from compas_cgal.booleans import boolean_difference_mesh_mesh

        mesh0: Mesh = target_geometry.copy() if not isinstance(target_geometry, Brep) else Mesh.from_polygons(target_geometry.to_polygons())
        mesh1: Mesh = source_geometry.copy() if not isinstance(source_geometry, Brep) else Mesh.from_polygons(source_geometry.to_polygons())

        A = mesh0.to_vertices_and_faces(triangulated=True)
        B = mesh1.to_vertices_and_faces(triangulated=True)
        V, F = boolean_difference_mesh_mesh(A, B)
        return Mesh.from_vertices_and_faces(V, F) if V and F else mesh0
