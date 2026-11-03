from compas.datastructures import Mesh
from compas.geometry import Brep


def is_geometry_empty(geometry: Mesh | Brep) -> bool:
    """Determine whether model geometry contains no geometric content.

    Parameters
    ----------
    geometry
        Mesh or BRep geometry.

    Returns
    -------
    bool
        ``True`` if a mesh has no vertices or a BRep has no topology.

    Notes
    -----
    Empty geometry is a valid evaluated result, for example when a Boolean
    difference removes an entire target. It is distinct from missing geometry.

    """
    if isinstance(geometry, Mesh):
        return geometry.number_of_vertices() == 0
    if isinstance(geometry, Brep):
        return not geometry.vertices and not geometry.edges and not geometry.faces
    raise TypeError("Geometry emptiness requires a Mesh or BRep representation.")
